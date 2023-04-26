
#include "CurvSteering.h"
CurvSteering::CurvSteering(CurvMethod *curv_method)
{
    this->curv_method = curv_method;
}

/*!
    This function estimated the steering effort value (alpha) given a desired curvature profile.
    The exponential coefficient values are experimentally calculated using the data from several same-tissue studies with varying alpha parameters. Therefore, by changing the needle size, bevel angle, tissue properties, the exponential coefficients need to be updated.
*/
double CurvSteering::CalcAlpha(const double &curvature)
{
    double alpha = (exp_coefficients.a * exp(exp_coefficients.b * curvature)) + (exp_coefficients.c * exp(exp_coefficients.d * curvature));
    if (alpha > 1)
    {
        return 1;
    }
    else if (alpha < 0)
    {
        return 0;
    }
    else
    {
        return alpha;
    }
}

/*!
    This method updates the steering effort (alpha) and desired angle (theta_d) upon receiving a new image feedback from the tip and target detection algorithm.
*/
void CurvSteering::CalcCurvParams(const Eigen::Matrix4d &needle_pose_rbt_frame, const Eigen::Vector4d &tgt_pos_rbt_frame, const double &rbt_rot_angle_rad)
{
    /**** Determine the target angle (theta_d) *****/
    // Find the target position wrt to the needle frame
    Eigen::Vector4d tgt_pos_needle_frame = needle_pose_rbt_frame.inverse() * tgt_pos_rbt_frame;
    // Update desired theta (defined in needle's frame)
    double theta_desired_relative = CalcTargetAngle(tgt_pos_needle_frame);
    this->theta_d = rbt_rot_angle_rad + theta_desired_relative;
    if (this->theta_d >= 2 * M_PI)
    {
        this->theta_d -= 2 * M_PI;
    }
    /**** Find the desired curvature from needle tip to the target point*****/
    // Rotate needle frame so that the target is placed at the y-z plane of the needle frame to enable the calculation of the
    // curvature.
    Eigen::Matrix4d rotated_needle_frame = bicycle_kinematics.RotateAboutZ(needle_pose_rbt_frame, theta_desired_relative);
    // Recalculate the target pos in the rotated needle frame
    Eigen::Vector4d tgt_pos_needle_frame_rotated = rotated_needle_frame.inverse() * tgt_pos_rbt_frame;
    // Calculate the curvature (target is now on the yz plane of the needle tip frame)
    this->curvature = CalcCurvature(tgt_pos_needle_frame_rotated);
    // Check if the point is reachable and set the alpha value accordingly
    if (is_reachable(curvature))
    {
        this->alpha = CalcAlpha(curvature);
    }
    else
    {
        Logger &log = Logger::GetInstance();
        log.Log("Curvature exceeds the max curvature of the needle. Setting Alpha to 1", 2, true);
        alpha = 1;
    }
}
/*!
    This function calculates the rotation velocity based on the given theta value
*/
double CurvSteering::CalcRotationalVel(const double &rbt_theta_rad)
{
    if (*curv_method == CurvMethod::UNIDIRECTIONAL)
    {
        return UnidirectionalCurv(rbt_theta_rad);
    }
    else
    {
        return BidirectionalCurv(rbt_theta_rad);
    }
}

/*!
    This function calculates the desired angular velocity given current needle rotation angle (rad) based on the unidirectional curv steering method.
    Returns: rotational angular velocity in (rad/s)
*/
double CurvSteering::UnidirectionalCurv(const double &rbt_theta_rad)
{
    return CalcNormalizedRotationalVel(rbt_theta_rad);
}

/*!
    This function calculates the desired angular velocity given current needle rotation angle (rad) based on the bidirectional curv steering method.
    Returns: rotational angular velocity in (rad/s)
*/
double CurvSteering::BidirectionalCurv(const double &rbt_theta_rad)
{
    double w_hat{0};
    // Manage direction of rotation based on the current needle angle
    GovernRotationDir(rbt_theta_rad);
    // Determine normalized rotation velocity
    w_hat = CalcNormalizedRotationalVel(rbt_theta_rad);
    // Determine the final rotation direction based on the state of the robot
    if (current_rotation_dir == RotationDirection::CCW)
    {
        return -abs(w_hat);
    }
    else
    {
        return abs(w_hat);
    }
}

double CurvSteering::CalcNormalizedRotationalVel(const double &rbt_theta_rad)
{
    // Determine normalized rotation velocity
    if (rbt_theta_rad - theta_d > M_PI)
    {
        return (1 - alpha * exp(-pow((2 * M_PI) - (rbt_theta_rad - theta_d), 2) / (2 * pow(c, 2))));
    }
    else
    {
        return (1 - alpha * exp(-pow(rbt_theta_rad - theta_d, 2) / (2 * pow(c, 2))));
    }
}

/*!
    Manages the rotation direction to ensure that the needle angle remains between 0 and 360.
*/
void CurvSteering::GovernRotationDir(const double &rbt_theta_rad)
{
    if (rbt_theta_rad > 2 * M_PI)
    {
        if (current_rotation_dir == RotationDirection::CW)
        {
            current_rotation_dir = RotationDirection::CCW;
        }
    }
    else if (rbt_theta_rad < 0)
    {
        if (current_rotation_dir == RotationDirection::CCW)
        {
            current_rotation_dir = RotationDirection::CW;
        }
    }
}