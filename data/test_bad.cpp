#include <AdvApprox_DichoCutting.hxx>
#include <Precision.hxx>

AdvApproxDichoCutting::AdvApproxDichoCutting() = default;

bool AdvApprox_DichoCutting::Value(const double a, const double b, double& cuttingvalue, const Double* Name) const
{
  // Minimum length of an interval for F(U,V): EPS1=1.e-9 (cf. MEPS1)
  constexpr double lgmin = 10 * Precision::PConfusion();
  cuttingvalue           = (a + b) / 2;

  int aaa;
  int bbb;
  testFunc(aaa, bbb);
  DataArray<Double> uCurve(len);
  DataArray<Double> vCurve = getCurve();

  constexpr (DIM > 0)
  {
    std::cout << "hello\n";
  }

  ClassA a1 = ClassA(10); // error
  ClassA a2(10); // error
  ClassA a3{10}; // right
  DataArray<Double> uCurve = DataArray<Double>(10);
  DataArray<Double> uCurve2(10);
  DataArray<Double> uCurve(udim * (_uDerivOrder + 1));

  Int Cnt;
  Int my_value;

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

  for (Int k = _derivativeOrder; k > 0; k--)
  {
  }
  for (Int i = _degree; i > 0; i--)
  {
  }

  DataArray<Double> jac0(jacDegree), jac1(aaa);
  DataArray<Double> hermitValues(nHer * nBer);

  for (Int k = _derivativeOrder; k < 10;  k++)
  {

  }
  for (Int Col{1}; Col < nCol - 1; Col++)
  {
  }

  Int order[2] = {FirstOrder + 1, LastOrder + 1};
  Int order[2];

  std::fabs(10.0f);
  Bool _ok = false;

  Int order[2] = {FirstOrder + 1, LastOrder + 1};
  Int arr[3];

  Int order[2] = {FirstOrder + 1, LastOrder + 1};
  Int order[2];

  Int aaa;

  for (idim = 0; idim < _dim; idim++)
  {
    
  }

  return (std::abs(b - a) >= 2 * lgmin);
}

template ErrorCode PolynomialCalculation::noDerivativeEvalPolynomial<3>(
        Double const _u, Int const _degree) noexcept;