#pragma once

#include <Standard.hxx>
#include <Standard_DefineAlloc.hxx>
#include <Standard_Handle.hxx>

#include <AdvApprox_Cutting.hxx>
#include <Standard_Boolean.hxx>
#include <Standard_Real.hxx>

//! if Cutting is necessary in [a,b], we cut at (a+b) / 2.
class AdvApproxDichoCutting : public AdvApproxCutting
{
public:

  AdvApprox_DichoCutting();

  ErrorCode value(Double const _a, Double const _b, Double& _cuttingValue, Double const* _name, Bool& _result) const override;
  ErrorCode value2(Int const _a);
  ErrorCode value3(Int const /* _aaa */);
  virtual ErrorCode toCoefficients(Int const _dim) const = 0;
  ErrorCode value4();

private:
  Int m_count;
  Double m_totalValue;
  Int m_size;
};

#endif // _AdvApprox_DichoCutting_HeaderFile
