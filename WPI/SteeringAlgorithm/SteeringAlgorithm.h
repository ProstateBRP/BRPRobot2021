#ifndef _STEERINGALGORITHM_H_
#define _STEERINGALGORITHM_H_
#include <Eigen/Dense>
#include "../Utilities/Timer/Timer.hpp"
#include "../Utilities/Logger/Logger.hpp"
#include "../NeedleKinematics/BicycleKinematics.h"

class SteeringAlgorithm
{
public:
    // Member functions
    double CalcCurvature(const Eigen::Vector4d &);
    double CalcTargetAngle(const Eigen::Vector4d &);
    bool is_reachable(const double &);

    // Member attributes
    BicycleKinematics bicycle_kinematics;
    double curvature{0};
};
#endif /*_STEERINGALGORITHM_H_*/