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

  AdvApproxDichoCutting();


  bool Value(const double a, const double b, double& cuttingvalue, const Double* Name) const override;
  void value2(Int _a);
  void value3(Int const /* aaa */);
  virtual void ToCoefficients(Int const _dim) const = 0;
  virtual void toCoefficients(Int const _dim) const = 0;

  void value4();

  // 	return 0;
  //  return 0
  void value5(Double& _result);

private:
  Int myCount;
  Double total_value;
  Int Size;
};

static FORCE_INLINE Int Index2dScalar(Int _row, Int _col, Int _nCol)
{
}


#endif // _AdvApprox_DichoCutting_HeaderFile
