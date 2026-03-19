
write python code in src to check the code style of .h and .cpp

example bad and good:

    data/test_bad.h  data/test_bad.cpp
    data/test_good.h  data/test_good.cpp



rules:
```txt
    1. never use int or double,  instead use Double and Int
        int a => Int a;
    2. all para need begin with _ and little camel
        Int myname =>  Int _myName
    3. all para with value pass input need add const, const after type
        Int _a =>  Int const _a
        const Int _a  =>  Int const _a;
    4. all const after type
    5. all input with const pointer need const after type
        const Double * _a  =>  Double* const _a;
    6. pointer with output keep
        Double* _output  => not change
    7. func name need little camel,  begin with lower capital.
    8. all variable declare with assignment need with {}
        Int a = 10;  => Int a{10};
        Int a, b = 10, c;  =>  Int a, b{10}, c;
    9. all function must retrn ErrorCode, 
        speciaficly, you should detect return type of Int, Double, void, boo
        they should return ErrorCode, and Double Int as reference
    10. all variable should be littel camel
    11. class memeber variable begin with m_littleCamelCase
    12. constexpr variable can start with upper case
    13. use space instead of tab
    14. func para use pointer for output, not use reference for output
```


python code to print the bad place with:
    line number
    line code
    ~~~ under bad code


implement:
```txt
1. you can implement by regex
2. but maybe you need more mature method that parse the grammar to ast, then analysis,
this is more stable way.
3. use test_bad and test_good to verify your code

```

use test_bad and test_good to verify your code




<!-- initValue(T const& /*coeff*/) -->
<!-- if constexpr (DIM > 0) -->

others:
```txt
1. para only apply to function declare, not for function call
2. not apply anything inside comment
3. if constexpr (DIM > 0) is not function declare, not function call
4. bool value2(Int _a);  input para need add const  Int _a;
5. DataArray<Double> uCurve(len);  object constructor using {} instead of ();
6. you miss variable declare, the type is template class
7. need also detect bad for complex constructor:  DataArray<Double> uCurve(udim * (_uDerivOrder + 1));
8. this is not func declare, nor function call:  else if (_workDegree < NDEG10)
9. why not detect this bad func name: virtual void ToCoefficients(Int const _dim) const = 0;
10. not function declare return std::sqrt(CalcSquaredNorm(_nSize, _value));
11. any function inside class with void nee change to ErrorCode :  void value4(); => ErrorCode value4();
12. void detect:  miss virtual void toCoefficients(Int const _dim) const = 0;
13. case 0: 0 is not variable
14. bug: DataArray<Double> hermitValues(nHer * nBer);
15: bug: DataArray<Double> jac0(jacDegree), jac1(aaa);
16: bug: delete m_jacobi;
17: constexpr variable can start with upper case
18: miss:  static FORCE_INLINE Int index2dScalar(Int _row, Int _col, Int _nCol)
        => static FORCE_INLINE Int index2dScalar(Int const _row, Int const _col, Int const _nCol)
19: miss: for (Int k = _derivativeOrder; k > ...);  
    =>  for (Int k{_derivativeOrder}; k > ...);  
```

