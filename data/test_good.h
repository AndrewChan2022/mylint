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

  ErrorCode value(Double const _a, Double const _b, Double* const _cuttingValue, Double const* _name, Bool* const _result) const override;
  ErrorCode value2(Int const _a);
  ErrorCode value3(Int const /* _aaa */);
  virtual ErrorCode toCoefficients(Int const _dim) const = 0;
  ErrorCode value4();

  // return 0;
  // return 0
  ErrorCode value5(Double* const _result);

private:
  Int m_count{0};
  Double m_totalValue{0.0};
  Int m_size{0};
};

#endif // _AdvApprox_DichoCutting_HeaderFile
