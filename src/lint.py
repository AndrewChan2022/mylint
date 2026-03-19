"""
C++ style checker based on project coding conventions.

Rules:
  1. Never use `int` or `double` — use `Int` and `Double` instead.
  2. All function parameters must begin with `_` and use lowerCamelCase.
  3. All value-pass input parameters need `const` after the type (not before).
  4. All const-pointer input parameters need `const` after the type (not before).
  5. Function names must be lowerCamelCase (begin with lowercase).
  6. Variable declarations with assignment must use `{}` not `=`, class init with {} not ()
  7. Functions must return `ErrorCode` (not void/int/double/bool).
  8. Local variables must be lowerCamelCase.
  9. Class member variables must begin with `m_` and use lowerCamelCase.
  10. Use spaces instead of tabs.
  11. Function output parameters must use pointer, not reference.
  12. Between `//` and comment content, exactly one space (no tab, no extra spaces).
  13. Class data members of plain old types must be initialized.
  14. Output pointer parameters must have `const` on the pointer (e.g. `Type* const _out`).
"""

import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Issue = (lineno, col_start, col_len, message)
#   col_start: 0-based column in the raw line
#   col_len:   length of the underlined span
# ---------------------------------------------------------------------------


def _strip_comments_and_strings(line: str) -> str:
    """Remove string literals and // comments from a line for analysis."""
    result = []
    i = 0
    in_string = None
    while i < len(line):
        ch = line[i]
        if in_string:
            if ch == '\\':
                i += 2
                continue
            if ch == in_string:
                in_string = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_string = ch
            i += 1
            continue
        if ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
            break
        result.append(ch)
        i += 1
    return ''.join(result)


def _is_preprocessor(line: str) -> bool:
    return line.lstrip().startswith('#')


def _is_camel_case(name: str) -> bool:
    if len(name) < 2:
        return True
    return any(c.isupper() for c in name[1:])


def _to_camel_case(name: str) -> str:
    return name


def _find_token(raw_line: str, token: str, start: int = 0) -> int:
    """Find the position of a whole-word token in raw_line."""
    pos = start
    while True:
        idx = raw_line.find(token, pos)
        if idx < 0:
            return -1
        # Check word boundaries
        before_ok = (idx == 0 or not raw_line[idx - 1].isalnum() and raw_line[idx - 1] != '_')
        end = idx + len(token)
        after_ok = (end >= len(raw_line) or not raw_line[end].isalnum() and raw_line[end] != '_')
        if before_ok and after_ok:
            return idx
        pos = idx + 1


# ---------------------------------------------------------------------------
# Rule checkers — each returns list of (lineno, col, length, message)
# ---------------------------------------------------------------------------

def check_rule10_no_tabs(raw_line: str, lineno: int) -> list:
    """Rule 10: use spaces instead of tabs."""
    issues = []
    for i, ch in enumerate(raw_line):
        if ch == '\t':
            issues.append(
                (lineno, i, 1, "Rule 10: use spaces instead of tabs")
            )
            break  # one issue per line is enough
    return issues


def check_rule12_comment_spacing(raw_line: str, lineno: int) -> list:
    """Rule 12: between // and comment content, exactly one space."""
    issues = []
    # Find // that is not inside a string (simple heuristic: first occurrence)
    idx = raw_line.find('//')
    if idx < 0:
        return issues
    # Skip if it's a /// (doxygen) or //! (doxygen) — those are fine
    rest = raw_line[idx + 2:]
    if not rest:
        return issues  # empty comment like `//` is fine
    # Check: if rest starts with '/' or '!' it's a doxygen comment — still check spacing after
    if rest[0] in ('/', '!'):
        rest = rest[1:]
        idx += 1
        if not rest:
            return issues
    # Now rest is everything after // (or //! or ///)
    # If the rest is all whitespace, it's fine (blank comment line)
    if not rest.strip():
        return issues
    # Check: should be exactly one space then non-space content
    if rest[0] == '\t':
        col = idx + 2
        issues.append(
            (lineno, col, 1,
             "Rule 12: use a single space after `//`, not a tab")
        )
    elif rest[0] != ' ':
        # No space at all: //content
        col = idx + 2
        issues.append(
            (lineno, col, 1,
             "Rule 12: add a space after `//` — e.g. `// comment`")
        )
    elif len(rest) >= 2 and rest[1] == ' ':
        # Multiple spaces: //  content
        col = idx + 2
        # Count how many spaces
        n_spaces = 0
        for ch in rest:
            if ch == ' ':
                n_spaces += 1
            else:
                break
        if n_spaces > 1:
            issues.append(
                (lineno, col, n_spaces,
                 f"Rule 12: use exactly one space after `//`, not {n_spaces}")
            )
    return issues


def check_rule1_primitive_types(line: str, lineno: int, raw_line: str) -> list:
    """Rule 1: never use bare `int` or `double`, use `Int`/`Double`."""
    issues = []
    if _is_preprocessor(raw_line):
        return issues
    stripped = line.strip()
    if stripped.startswith('constexpr '):
        return issues
    for prim, replacement in [('double', 'Double'), ('int', 'Int')]:
        search_start = 0
        for m in re.finditer(rf'\b{prim}\b', line):
            col = _find_token(raw_line, prim, search_start)
            if col < 0:
                col = m.start()
            else:
                search_start = col + len(prim)
            issues.append(
                (lineno, col, len(prim),
                 f"Rule 1: use `{replacement}` instead of `{prim}`")
            )
    return issues


def _parse_function_params(sig: str) -> list:
    """Extract individual parameter strings from a function signature."""
    depth = 0
    start = None
    end = None
    for i, ch in enumerate(sig):
        if ch == '(':
            if depth == 0:
                start = i
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                end = i
                break
    if start is None or end is None:
        return []
    params_str = sig[start + 1:end]
    if not params_str.strip():
        return []
    params = []
    depth = 0
    current = []
    for ch in params_str:
        if ch in ('<', '('):
            depth += 1
        elif ch in ('>', ')'):
            depth -= 1
        if ch == ',' and depth == 0:
            params.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        params.append(''.join(current).strip())
    return params


def _extract_param_name(param: str) -> str | None:
    p = param.strip()
    if not p:
        return None
    # Skip commented-out parameter names like /*coeff*/
    if re.search(r'/\*\s*\w+\s*\*/', p):
        return None
    if '=' in p:
        p = p[:p.index('=')].strip()
    if '{' in p:
        p = p[:p.index('{')].strip()
    tokens = p.replace('*', ' ').replace('&', ' ').split()
    if not tokens:
        return None
    name = tokens[-1]
    if name in ('const', 'volatile', 'override', 'final'):
        return None
    return name


def check_rule2_param_naming(params: list, lineno: int, raw_line: str) -> list:
    """Rule 2: all parameters must begin with `_` and use lowerCamelCase."""
    issues = []
    for param in params:
        name = _extract_param_name(param)
        if not name:
            continue
        col = _find_token(raw_line, name)
        if col < 0:
            col = 0
        if not name.startswith('_'):
            if len(name) > 1 and name.islower() and '_' not in name and not _is_camel_case(name):
                msg = (f"Rule 2: parameter `{name}` should start with `_` "
                       f"and use lowerCamelCase (e.g. `_{_to_camel_case(name)}`)")
            else:
                msg = f"Rule 2: parameter `{name}` should start with `_` (e.g. `_{name}`)"
            issues.append((lineno, col, len(name), msg))
        elif len(name) > 1 and name[1].isupper():
            issues.append(
                (lineno, col, len(name),
                 f"Rule 2: parameter `{name}` should use lowerCamelCase after `_`")
            )
    return issues


def check_rule3_const_after_type_value(params: list, lineno: int, raw_line: str) -> list:
    """Rule 3: value-pass input params need `const` after type.
    Flags both missing const and misplaced const (before type)."""
    issues = []
    for param in params:
        p = param.strip()
        if not p or '*' in p or '&' in p:
            continue
        name = _extract_param_name(param)
        if not name:
            continue
        has_const = 'const' in p
        if has_const and re.match(r'^\s*const\s+', p):
            # const before type — should be after
            col = -1
            name_col = _find_token(raw_line, name)
            if name_col > 0:
                segment = raw_line[:name_col]
                col = segment.rfind('const')
            if col < 0:
                col = raw_line.find('const')
            issues.append(
                (lineno, col, 5,
                 f"Rule 3: `const` should be after type, not before — "
                 f"e.g. `Type const {name}`")
            )
        elif not has_const:
            # const missing entirely — value param should have const
            col = _find_token(raw_line, name)
            if col < 0:
                col = 0
            # Find the type token before the name
            tokens = p.split()
            type_name = tokens[0] if tokens else 'Type'
            issues.append(
                (lineno, col, len(name),
                 f"Rule 3: value parameter `{name}` should be const — "
                 f"e.g. `{type_name} const {name}`")
            )
    return issues


def check_rule4_const_pointer(params: list, lineno: int, raw_line: str) -> list:
    """Rule 4: const pointer input — const after type, not before."""
    issues = []
    for param in params:
        p = param.strip()
        if not p or '*' not in p:
            continue
        if re.match(r'^\s*(const)\s+\w+\s*\*', p):
            name = _extract_param_name(param)
            col = -1
            if name:
                name_col = _find_token(raw_line, name)
                if name_col > 0:
                    segment = raw_line[:name_col]
                    col = segment.rfind('const')
            if col < 0:
                col = raw_line.find('const')
            issues.append(
                (lineno, col, 5,
                 f"Rule 4: const pointer — `const` should be after type, "
                 f"e.g. `Type const* {name or '...'}`")
            )
    return issues


def check_rule11_output_pointer(params: list, lineno: int, raw_line: str) -> list:
    """Rule 11: output parameters must use pointer, not reference.
    Non-const reference params like `Type& _name` should be `Type* _name`."""
    issues = []
    for param in params:
        p = param.strip()
        if not p or '&' not in p:
            continue
        # Skip const references — those are input params, not output
        if re.search(r'\bconst\b', p):
            continue
        # Match non-const reference: Type& name  or  Type &name
        if re.search(r'&', p):
            name = _extract_param_name(param)
            if not name:
                continue
            col = _find_token(raw_line, '&')
            if col < 0:
                col = _find_token(raw_line, name)
            if col < 0:
                col = 0
            issues.append(
                (lineno, col, 1,
                 f"Rule 11: output parameter `{name}` should use pointer "
                 f"instead of reference — e.g. `Type* {name}`")
            )
    return issues


def check_rule14_output_pointer_const(params: list, lineno: int, raw_line: str) -> list:
    """Rule 14: output pointer params must have const on the pointer.
    `Type* _out` should be `Type* const _out`."""
    issues = []
    for param in params:
        p = param.strip()
        if not p or '*' not in p:
            continue
        # Skip input const pointers (const before *): `Type const* _name` or `const Type* _name`
        # These are input params, Rule 4 handles them
        if re.match(r'^\s*const\s+\w+\s*\*', p) or re.search(r'\bconst\s*\*', p):
            continue
        # Now we have an output pointer like `Type* _name`
        # Check if it already has `const` after `*`: `Type* const _name`
        if re.search(r'\*\s+const\b', p) or re.search(r'\*const\b', p):
            continue
        name = _extract_param_name(param)
        if not name:
            continue
        col = _find_token(raw_line, '*')
        if col < 0:
            col = _find_token(raw_line, name)
        if col < 0:
            col = 0
        issues.append(
            (lineno, col, 1,
             f"Rule 14: output pointer `{name}` should have const on pointer "
             f"— e.g. `Type* const {name}`")
        )
    return issues


def _extract_func_name(line: str) -> str | None:
    s = line.strip()
    _KEYWORDS = {'if', 'for', 'while', 'switch', 'catch', 'return', 'sizeof',
                 'static_cast', 'dynamic_cast', 'reinterpret_cast', 'const_cast',
                 'class', 'struct', 'enum', 'union', 'namespace', 'template',
                 'constexpr', 'decltype', 'noexcept', 'override', 'final',
                 'delete', 'default', 'explicit', 'virtual', 'inline',
                 'std', 'abs'}
    m = re.search(r'(\w+)\s*::\s*(\w+)\s*\(', s)
    if m:
        class_name = m.group(1)
        method_name = m.group(2)
        if method_name in _KEYWORDS:
            return None
        if method_name == class_name:
            return None
        return method_name
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline|virtual|explicit)\s+)*'
        r'(\w+(?:::\w+)*[*&\s]*)\s+(\w+)\s*\(',
        s
    )
    if m:
        name = m.group(2)
        if name in _KEYWORDS:
            return None
        return name
    return None


def _is_constructor_or_destructor(line: str, func_name: str) -> bool:
    if re.search(rf'\b{re.escape(func_name)}\s*::\s*~?\s*{re.escape(func_name)}\s*\(', line):
        return True
    stripped = line.strip()
    if re.match(rf'^\s*~?\s*{re.escape(func_name)}\s*\(', stripped):
        return True
    return False


_BAD_RETURN_TYPES = {
    'void': ('ErrorCode', None),
    'int': ('ErrorCode', 'Int& output param'),
    'Int': ('ErrorCode', 'Int& output param'),
    'double': ('ErrorCode', 'Double& output param'),
    'Double': ('ErrorCode', 'Double& output param'),
    'bool': ('ErrorCode', 'bool& output param'),
}


def check_rule7_return_type(line: str, lineno: int, raw_line: str) -> list:
    """Rule 7: functions must return ErrorCode.
    void/int/Int/double/Double return types should be ErrorCode,
    with value types passed out via reference parameters instead."""
    issues = []
    s = line.strip()
    # Match: [qualifiers] returnType funcName(
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline|virtual|explicit)\s+)*'
        r'(\w+)\s+(?:\w+\s*::\s*~?\s*)?\w+\s*\(',
        s
    )
    if not m:
        return issues
    ret_type = m.group(1)
    if ret_type not in _BAD_RETURN_TYPES:
        return issues
    replacement, hint = _BAD_RETURN_TYPES[ret_type]
    col = _find_token(raw_line, ret_type)
    if col < 0:
        col = 0
    msg = f"Rule 7: use `{replacement}` instead of `{ret_type}` return type"
    if hint:
        msg += f" — pass result as `{hint}`"
    issues.append((lineno, col, len(ret_type), msg))
    return issues


def check_rule5_func_name(line: str, lineno: int, raw_line: str) -> list:
    """Rule 5: function names must be lowerCamelCase (start with lowercase)."""
    issues = []
    func_name = _extract_func_name(line)
    if not func_name:
        return issues
    if _is_constructor_or_destructor(line, func_name):
        return issues
    if func_name[0].isupper():
        suggested = func_name[0].lower() + func_name[1:]
        col = _find_token(raw_line, func_name)
        if col < 0:
            col = 0
        issues.append(
            (lineno, col, len(func_name),
             f"Rule 5: function `{func_name}` should start with "
             f"lowercase (e.g. `{suggested}`)")
        )
    return issues


def check_rule6_brace_init(line: str, lineno: int, raw_line: str) -> list:
    """Rule 6: variable declarations with assignment should use {} not =.
    Also catches constructor-style init: Type var(args) => Type var{args}."""
    issues = []
    if _is_preprocessor(raw_line):
        return issues
    stripped = line.strip()
    if stripped.startswith('return ') or stripped.startswith('using '):
        return issues

    # Check 1: assignment init  Type var = value;
    if '=' in stripped:
        has_compound = False
        for op in ('==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=', '&=',
                   '|=', '^=', '<<=', '>>=', '=>'):
            if op in stripped:
                has_compound = True
                break
        if not has_compound:
            m = re.match(
                r'^(?:(?:static|constexpr|const|volatile|inline)\s+)*'
                r'(\w+(?:::\w+)*(?:<[^>]*>)?)\s+'  # type, possibly with template
                r'(\w+)\s*'
                r'=\s*'
                r'(.+?)\s*;',
                stripped
            )
            if m:
                var_name = m.group(2)
                value = m.group(3)
                if '{' not in value:
                    name_col = _find_token(raw_line, var_name)
                    eq_col = raw_line.find('=', name_col + len(var_name) if name_col >= 0 else 0)
                    if eq_col < 0:
                        eq_col = 0
                    semi_col = raw_line.find(';', eq_col)
                    span = (semi_col - eq_col) if semi_col > eq_col else len(value) + 2
                    issues.append(
                        (lineno, eq_col, span,
                         f"Rule 6: use brace initialization — "
                         f"`{var_name}{{{value}}}` instead of `{var_name} = {value}`")
                    )

    # Check 2: constructor-style init  Type var(args);  =>  Type var{args};
    # Handles multi-var: Type v1(a), v2(b);
    # Must NOT be a function declaration (those have typed params).
    if '(' in stripped and not _is_function_decl(stripped):
        m = re.match(
            r'^(?:(?:static|constexpr|const|volatile|inline)\s+)*'
            r'(\w+(?:::\w+)*(?:<[^>]*>)?)\s+'  # type, possibly with template
            r'(.+?)\s*;',                        # rest before semicolon
            stripped
        )
        if m:
            rest = m.group(2)
            # Split rest by comma at depth 0, respecting parens/braces
            parts = []
            depth = 0
            current = []
            for ch in rest:
                if ch in ('(', '{', '<'):
                    depth += 1
                elif ch in (')', '}', '>'):
                    depth -= 1
                if ch == ',' and depth == 0:
                    parts.append(''.join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append(''.join(current).strip())
            # Check each part for constructor-style init: varName(args)
            for part in parts:
                pm = re.match(r'^(\w+)\s*\(', part)
                if not pm:
                    continue
                var_name = pm.group(1)
                # Find balanced closing paren
                paren_start = part.index('(')
                depth = 0
                paren_end = None
                for ci in range(paren_start, len(part)):
                    if part[ci] == '(':
                        depth += 1
                    elif part[ci] == ')':
                        depth -= 1
                        if depth == 0:
                            paren_end = ci
                            break
                if paren_end is None:
                    continue
                # Everything after ) in this part should be empty
                trailing = part[paren_end + 1:].strip()
                if trailing:
                    continue
                args = part[paren_start + 1:paren_end]
                # Skip if args look like typed parameters (function declaration)
                params = [p.strip() for p in args.split(',') if p.strip()]
                looks_like_decl = all(
                    re.match(r'^(?:const\s+)?\w+(?:::\w+)*(?:\s+const)?\s*(?:[*&]\s*)?\s+\w+$', p)
                    and not re.search(r'\s[*]\s', p)
                    for p in params
                ) if params else False
                if not looks_like_decl:
                    raw_paren_col = raw_line.find('(', _find_token(raw_line, var_name) or 0)
                    if raw_paren_col < 0:
                        raw_paren_col = 0
                    # Find the matching ) in raw_line
                    depth = 0
                    raw_paren_end = raw_paren_col
                    for ci in range(raw_paren_col, len(raw_line)):
                        if raw_line[ci] == '(':
                            depth += 1
                        elif raw_line[ci] == ')':
                            depth -= 1
                            if depth == 0:
                                raw_paren_end = ci
                                break
                    span = raw_paren_end - raw_paren_col + 1
                    issues.append(
                        (lineno, raw_paren_col, span,
                         f"Rule 6: use brace initialization — "
                         f"`{var_name}{{{args}}}` instead of `{var_name}({args})`")
                    )

    return issues


def _is_lower_camel_case(name: str) -> bool:
    """Check if name is lowerCamelCase: starts lowercase, no underscores."""
    if not name or not name[0].islower():
        return False
    if '_' in name:
        return False
    return True


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to lowerCamelCase."""
    parts = name.split('_')
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:] if p)


def check_rule8_local_var_naming(line: str, lineno: int, raw_line: str) -> list:
    """Rule 8: local variables must be lowerCamelCase."""
    issues = []
    if _is_preprocessor(raw_line):
        return issues
    stripped = line.strip()
    # Skip lines that are not variable declarations
    if stripped.startswith('return ') or stripped.startswith('using '):
        return issues
    # Skip control flow
    for kw in ('if', 'for', 'while', 'switch', 'catch', 'else', 'case',
               'if constexpr', 'constexpr'):
        if re.match(rf'(?:^|.*\s){re.escape(kw)}\s*[\({{]', stripped):
            return issues
    # Skip function declarations — params are checked by Rule 2
    if _is_function_decl(stripped):
        return issues
    # constexpr variables are allowed to start with uppercase
    if stripped.startswith('constexpr '):
        return issues
    # Match variable declarations: [qualifiers] Type varName [;{=(,]
    # Also handle multi-var declarations: Type a, b, c;
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline)\s+)*'
        r'(\w+(?:::\w+)*(?:<[^>]*>)?)\s+'  # type (possibly template)
        r'(.+?)\s*;',                       # rest before semicolon
        stripped
    )
    if not m:
        return issues
    type_name = m.group(1)
    # Skip if the "type" is actually a keyword or function call
    _SKIP_TYPES = {'return', 'using', 'class', 'struct', 'enum', 'union',
                   'namespace', 'template', 'typedef', 'typename', 'goto',
                   'case', 'default', 'delete', 'new', 'throw'}
    if type_name in _SKIP_TYPES:
        return issues
    rest = m.group(2)
    # Split by comma for multi-var declarations, respecting braces/parens
    vars_list = []
    depth = 0
    current = []
    for ch in rest:
        if ch in ('(', '{', '<'):
            depth += 1
        elif ch in (')', '}', '>'):
            depth -= 1
        if ch == ',' and depth == 0:
            vars_list.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        vars_list.append(''.join(current).strip())

    for var_part in vars_list:
        # Extract variable name from each part (before =, {, or ()
        vm = re.match(r'([*&\s]*)?(\w+)', var_part)
        if not vm:
            continue
        var_name = vm.group(2)
        # Skip if it's a keyword
        if var_name in ('const', 'volatile', 'override', 'final', 'default', 'delete'):
            continue
        if not _is_lower_camel_case(var_name):
            col = _find_token(raw_line, var_name)
            if col < 0:
                col = 0
            if '_' in var_name:
                suggested = _snake_to_camel(var_name)
                msg = (f"Rule 8: variable `{var_name}` should be lowerCamelCase "
                       f"(e.g. `{suggested}`)")
            elif var_name[0].isupper():
                suggested = var_name[0].lower() + var_name[1:]
                msg = (f"Rule 8: variable `{var_name}` should start with "
                       f"lowercase (e.g. `{suggested}`)")
            else:
                msg = f"Rule 8: variable `{var_name}` should be lowerCamelCase"
            issues.append((lineno, col, len(var_name), msg))
    return issues


def _is_member_var_line(line: str) -> bool:
    """Check if line looks like a class member variable declaration."""
    stripped = line.strip()
    if not stripped or stripped.startswith('//') or stripped.startswith('#'):
        return False
    if _is_function_decl(stripped):
        return False
    # Skip access specifiers, labels, etc.
    if re.match(r'^(public|private|protected)\s*:', stripped):
        return False
    if stripped in ('{', '}', '};'):
        return False
    # Skip using, typedef, friend, class/struct/enum fwd decls
    for kw in ('using ', 'typedef ', 'friend ', 'class ', 'struct ', 'enum ',
               'template', 'namespace', 'return ', 'delete ', 'new ', 'throw '):
        if stripped.startswith(kw):
            return False
    # Must look like a variable declaration: Type varName [;{=]
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline|mutable)\s+)*'
        r'\w+(?:::\w+)*(?:<[^>]*>)?\s+'  # type
        r'\w+',                           # variable name
        stripped
    )
    return m is not None


def _extract_var_names(line: str) -> list:
    """Extract variable names from a declaration line. Returns list of names."""
    stripped = line.strip()
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline|mutable)\s+)*'
        r'(\w+(?:::\w+)*(?:<[^>]*>)?)\s+'  # type
        r'(.+?)\s*;',                       # rest before semicolon
        stripped
    )
    if not m:
        return []
    rest = m.group(2)
    # Split by comma respecting braces/parens
    vars_list = []
    depth = 0
    current = []
    for ch in rest:
        if ch in ('(', '{', '<'):
            depth += 1
        elif ch in (')', '}', '>'):
            depth -= 1
        if ch == ',' and depth == 0:
            vars_list.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        vars_list.append(''.join(current).strip())
    names = []
    for var_part in vars_list:
        vm = re.match(r'([*&\s]*)?(\w+)', var_part)
        if vm:
            name = vm.group(2)
            if name not in ('const', 'volatile', 'override', 'final', 'default', 'delete'):
                names.append(name)
    return names


_POD_TYPES = {'Int', 'Double', 'Bool', 'int', 'double', 'bool', 'float',
               'char', 'short', 'long', 'unsigned', 'signed', 'size_t',
               'Int32', 'Int64', 'UInt32', 'UInt64'}


def check_rule13_member_pod_init(line: str, lineno: int, raw_line: str) -> list:
    """Rule 13: class data members of plain old types must be initialized."""
    issues = []
    if not _is_member_var_line(line):
        return issues
    stripped = line.strip()
    # Extract the type
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline|mutable)\s+)*'
        r'(\w+(?:::\w+)*)\s+'
        r'(.+?)\s*;',
        stripped
    )
    if not m:
        return issues
    type_name = m.group(1)
    if type_name not in _POD_TYPES:
        return issues
    rest = m.group(2)
    # Split by comma for multi-var declarations
    vars_list = []
    depth = 0
    current = []
    for ch in rest:
        if ch in ('(', '{', '<'):
            depth += 1
        elif ch in (')', '}', '>'):
            depth -= 1
        if ch == ',' and depth == 0:
            vars_list.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        vars_list.append(''.join(current).strip())
    for var_part in vars_list:
        # Check if this var has initialization ({...} or = ...)
        if '{' in var_part or '=' in var_part:
            continue
        vm = re.match(r'([*&\s]*)?(\w+)', var_part)
        if not vm:
            continue
        var_name = vm.group(2)
        if var_name in ('const', 'volatile', 'override', 'final', 'default', 'delete'):
            continue
        col = _find_token(raw_line, var_name)
        if col < 0:
            col = 0
        issues.append(
            (lineno, col, len(var_name),
             f"Rule 13: member `{var_name}` of type `{type_name}` must be "
             f"initialized — e.g. `{type_name} {var_name}{{0}}`")
        )
    return issues


def check_rule9_member_var_naming(line: str, lineno: int, raw_line: str) -> list:
    """Rule 9: class member variables must begin with m_ and use lowerCamelCase."""
    issues = []
    if not _is_member_var_line(line):
        return issues
    names = _extract_var_names(line)
    for var_name in names:
        col = _find_token(raw_line, var_name)
        if col < 0:
            col = 0
        if not var_name.startswith('m_'):
            # Suggest m_ + lowerCamelCase version
            if '_' in var_name:
                base = _snake_to_camel(var_name)
            elif var_name[0].isupper():
                base = var_name[0].lower() + var_name[1:]
            else:
                base = var_name
            suggested = f"m_{base}"
            msg = (f"Rule 9: member variable `{var_name}` should start with "
                   f"`m_` (e.g. `{suggested}`)")
            issues.append((lineno, col, len(var_name), msg))
        else:
            # Has m_ prefix — check that the rest is lowerCamelCase
            rest = var_name[2:]
            if rest and not _is_lower_camel_case(rest):
                if '_' in rest:
                    suggested = f"m_{_snake_to_camel(rest)}"
                elif rest[0].isupper():
                    suggested = f"m_{rest[0].lower()}{rest[1:]}"
                else:
                    suggested = var_name
                msg = (f"Rule 9: member variable `{var_name}` after `m_` should be "
                       f"lowerCamelCase (e.g. `{suggested}`)")
                issues.append((lineno, col, len(var_name), msg))
    return issues


def _is_function_decl(line: str) -> bool:
    """Return True only for function declarations/definitions, not calls."""
    s = line.strip()
    if '(' not in s:
        return False
    # Skip control flow and assignments
    # `return` can have expressions before `(`, so match it as a prefix
    if re.match(r'^\s*return\b', s):
        return False
    for kw in ('if', 'for', 'while', 'switch', 'catch', 'sizeof',
                'if constexpr', 'constexpr', 'else if'):
        if re.match(rf'(?:^|.*\s){re.escape(kw)}\s*\(', s):
            return False
    # Skip variable assignments, but allow pure virtual `= 0`, `= default`, `= delete`
    if re.search(r'\w\s*=\s*', s):
        if not re.search(r'=\s*(0|default|delete)\s*;', s):
            return False
    # Must have a return type before the function name (declaration, not call)
    # Pattern: [qualifiers] returnType [Class::]funcName(params)
    m = re.match(
        r'^(?:(?:static|constexpr|const|volatile|inline|virtual|explicit)\s+)*'
        r'\w+(?:::\w+)*[*&\s]+'           # return type
        r'(?:\w+\s*::\s*~?\s*)?'           # optional Class:: prefix
        r'\w+\s*\(',
        s
    )
    if m:
        # Verify the args look like typed parameters, not values/expressions
        # Extract args using balanced parens
        paren_start = s.index('(', m.start())
        depth = 0
        paren_end = None
        for ci in range(paren_start, len(s)):
            if s[ci] == '(':
                depth += 1
            elif s[ci] == ')':
                depth -= 1
                if depth == 0:
                    paren_end = ci
                    break
        if paren_end is not None:
            args = s[paren_start + 1:paren_end]
            params = [p.strip() for p in args.split(',') if p.strip()]
            # If all args are literals or simple expressions, it's a constructor call
            all_values = all(
                re.match(r'^[\d.\-+]+$', p) or  # numeric literal
                re.match(r'^\w+$', p) and not re.match(r'^(?:const|volatile|int|double|float|bool|char|void|Int|Double)\b', p)
                for p in params
            ) if params else False
            if all_values and not any(
                re.match(r'^(?:const\s+)?\w+(?:::\w+)*(?:\s+const)?\s*(?:[*&]\s*)?\s+\w+', p)
                and not re.search(r'\s[*]\s', p)
                for p in params
            ):
                return False
        return True
    # In-class declaration without explicit class prefix: `Type funcName(...)`
    # but NOT standalone calls like `funcName(...)` — require a type before name
    return False


def lint_file(filepath: str) -> list:
    """Run all lint checks on a file.
    Returns list of (line_number, col, length, message) and the raw lines."""
    path = Path(filepath)
    raw_lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    issues = []

    # Track context: stack of 'class' or 'other' for each brace level
    context_stack = []  # each entry: 'class' or 'other'
    pending_class = False  # True when we've seen class/struct but not yet its {

    for i, raw_line in enumerate(raw_lines, start=1):
        line = _strip_comments_and_strings(raw_line)
        stripped = line.strip()

        # Detect class/struct declaration (the { may be on same or next line)
        if re.match(
            r'^(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+\w+', stripped
        ):
            pending_class = True

        # Count braces on this line to update context
        for ch in stripped:
            if ch == '{':
                if pending_class:
                    context_stack.append('class')
                    pending_class = False
                else:
                    context_stack.append('other')
            elif ch == '}':
                if context_stack:
                    context_stack.pop()
                pending_class = False

        # Determine if we're directly inside a class body (not nested in a function)
        in_class_body = (len(context_stack) > 0 and context_stack[-1] == 'class')

        issues.extend(check_rule10_no_tabs(raw_line, i))
        issues.extend(check_rule12_comment_spacing(raw_line, i))
        issues.extend(check_rule1_primitive_types(line, i, raw_line))
        issues.extend(check_rule6_brace_init(line, i, raw_line))

        if in_class_body:
            issues.extend(check_rule9_member_var_naming(line, i, raw_line))
            issues.extend(check_rule13_member_pod_init(line, i, raw_line))
        else:
            issues.extend(check_rule8_local_var_naming(line, i, raw_line))

        if _is_function_decl(line):
            issues.extend(check_rule5_func_name(line, i, raw_line))
            issues.extend(check_rule7_return_type(line, i, raw_line))
            params = _parse_function_params(line)
            issues.extend(check_rule2_param_naming(params, i, raw_line))
            issues.extend(check_rule3_const_after_type_value(params, i, raw_line))
            issues.extend(check_rule4_const_pointer(params, i, raw_line))
            issues.extend(check_rule11_output_pointer(params, i, raw_line))
            issues.extend(check_rule14_output_pointer_const(params, i, raw_line))

    return issues, raw_lines


_EXTENSIONS = {'.h', '.hpp', '.hxx', '.inl', '.cpp', '.cxx', '.cc'}


def collect_files(args: list) -> list:
    """Collect C++ source files from a mix of files and directories."""
    files = []
    for arg in args:
        p = Path(arg)
        if p.is_dir():
            for ext in _EXTENSIONS:
                files.extend(sorted(p.rglob(f'*{ext}')))
        elif p.is_file() and p.suffix in _EXTENSIONS:
            files.append(p)
        elif p.is_file():
            files.append(p)  # allow explicit files regardless of extension
    return files


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <file_or_dir> [...]")
        print(f"  Scans .h .hpp .hxx .inl .cpp .cxx .cc files recursively in directories.")
        sys.exit(1)

    all_files = collect_files(sys.argv[1:])
    if not all_files:
        print("No matching files found.")
        sys.exit(0)

    total_issues = 0
    for filepath in all_files:
        issues, raw_lines = lint_file(str(filepath))
        if issues:
            print(f"\n{filepath}:")
            # Group issues by line number, preserving order
            from collections import OrderedDict
            by_line = OrderedDict()
            for lineno, col, length, msg in sorted(issues):
                by_line.setdefault(lineno, []).append((col, length, msg))

            for lineno, line_issues in by_line.items():
                raw = raw_lines[lineno - 1] if lineno <= len(raw_lines) else ''
                prefix = f"  line {lineno}| "
                print(f"{prefix}{raw}")

                # Build one combined underline covering all errors
                markers = [False] * len(raw)
                for col, length, _msg in line_issues:
                    for c in range(col, min(col + max(length, 1), len(raw))):
                        markers[c] = True
                underline = ''.join('~' if m else ' ' for m in markers)
                print(f"{' ' * len(prefix)}{underline}")

                # Then list each error message
                for idx, (col, length, msg) in enumerate(line_issues, 1):
                    print(f"{' ' * len(prefix)}  {idx}. {msg}")
                print()
            total_issues += len(issues)
        else:
            print(f"\n{filepath}: OK")

    print(f"{'='*60}")
    print(f"Total issues: {total_issues}")
    sys.exit(1 if total_issues > 0 else 0)


if __name__ == '__main__':
    main()
