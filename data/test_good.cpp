#include <AdvApprox_DichoCutting.hxx>
#include <Precision.hxx>

AdvApproxDichoCutting::AdvApproxDichoCutting() = default;

ErrorCode AdvApproxDichoCutting::value(Double const _a, Double const _b, Double* const _cuttingValue, Double const* _name, Bool* const _result) const
{
  // Minimum length of an interval for F(U,V): EPS1=1.e-9 (cf. MEPS1)
  constexpr double lgmin{10 * Precision::PConfusion()};
  _cuttingValue           = (_a + _b) / 2;

  Int aaa{};
  Int bbb{};
  testFunc(aaa, bbb);
  DataArray<Double> uCurve{len};
  DataArray<Double> vCurve{getCurve()};

  if constexpr (DIM > 0)
  {
    std::cout << "hello\n";
  }

  ClassA a1{10}; // error
  ClassA a2{10}; // error
  ClassA a3{10}; // right
  DataArray<Double> uCurve{10};
  DataArray<Double> uCurve2{10};
  DataArray<Double> uCurve{udim * (_uDerivOrder + 1)};

  Int cnt{};
  Int myVvalue{};

  Int a{0};
  switch (a)
  {
  case 0: break;
  case 1: break;
  default:break;
  }

  constexpr Int A{0};


  if (_workDegree < NDEG11)
  {

  }
  else if (_workDegree < NDEG10)
  {
    return std::sqrt(CalcSquaredNorm(_nSize, _value));
  }

  delete m_a;

  for (Int k{_derivativeOrder}; k > 0; k--)
  {
  }
  for (Int i{_degree}; i > 0; i--)
  {
  }

  DataArray<Double> jac0{jacDegree}, jac1{aaa, 0.0};
  DataArray<Double> hermitValues{nHer * nBer};

  for (Int k{_derivativeOrder}; k < 10;  k++)
  {
    
  }

  Int order[2]{FirstOrder + 1, LastOrder + 1};
  Int arr[3]{};

  Int aaa{};

  for (idim{0}; idim < _dim; idim++)
  {
    
  }

  return (Math::abs(_b - _a) >= 2 * lgmin);
}
