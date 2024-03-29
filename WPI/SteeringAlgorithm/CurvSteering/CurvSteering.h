#ifndef _CURVSTEERING_H_
#define _CURVSTEERING_H_
#include <math.h>
#include <string>
#include <iostream>
#include "Eigen/Dense"
#include "../SteeringAlgorithm.h"
/*!
    Coefficients are related to the 2nd degree exponential function.
    val(x) = a*exp(b*x) + c*exp(d*x)
    The coefficients are calculated using matlab fit function using 'exp2' flag.
    The real experimental data using needle insertion at various alpha values into a specific phantom/tissue are required to populate the data for calculation of the coefficients.
*/
struct ExponentialModelCoefficients
{
    double a = 1.082;
    double b = -11.17;
    double c = -1.08;
    double d = -842.8;
};

enum CurvMethod
{
    UNIDIRECTIONAL = 0,
    BIDIRECTIONAL = 1,

};
enum RotationDirection
{
    CCW = -1,
    CW = 1,
};

class CurvSteering : public SteeringAlgorithm
{
public:
    // Member functions
    CurvSteering(CurvMethod *);
    void CalcCurvParams(const Eigen::Matrix4d &, const Eigen::Vector4d &, const double &);
    double CalcAlpha(const double &);
    double UnidirectionalCurv(const double &);
    double BidirectionalCurv(const double &);
    double CalcRotationalVel(const double &);
    double CalcNormalizedRotationalVel(const double &);
    void GovernRotationDir(const double &);

    // Member attributes
    ExponentialModelCoefficients exp_coefficients;
    RotationDirection current_rotation_dir{CW};
    CurvMethod *curv_method;
    double theta_d{0};
    double alpha{0.0};
    double c{60 * M_PI / 180};
};

#endif /*_CURVSTEERING_H_*/