#include "SteeringAlgorithm.h"

/*!
    Calculates the curvature from the needle tip frame to the target point defined in the needle tip frame.
*/
double SteeringAlgorithm::CalcCurvature(const Eigen::Vector4d &tgt_position_needle_frame)
{
    return abs(1 / (tgt_position_needle_frame(1) / 2 + pow(tgt_position_needle_frame(2), 2) / (2 * tgt_position_needle_frame(1))));
}

/*!
    Calculate angle of the target as seen in the x-y plane of the needle frame.
    0 radians corresponds with negative y-axis.
    Return value is in radians.
*/
double SteeringAlgorithm::CalcTargetAngle(const Eigen::Vector4d &tgt_pt_needle_frame)
{
    return (atan2(-tgt_pt_needle_frame(0), tgt_pt_needle_frame(1)) + M_PI);
}

/*!
    Checks if the calculated curvature for a given target is feasible.
    curvature: Calculated curvature from the needle tip to the target location.
    Return: 1 if target is reachable, 0 if not.
*/
bool SteeringAlgorithm::is_reachable(const double &curvature)
{
    return bicycle_kinematics.max_curvature > curvature;
}
