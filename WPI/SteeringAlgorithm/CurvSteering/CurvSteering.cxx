
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
    // Update theta difference value
    set_theta_diff(rbt_rot_angle_rad);
    // Find the target position wrt to the needle frame
    Eigen::Vector4d tgt_pos_needle_frame = needle_pose_rbt_frame.inverse() * tgt_pos_rbt_frame;
    // Update desired theta (defined in needle's frame)
    this->theta_d = CalcTargetAngle(tgt_pos_needle_frame);
    // Find the desired curvature from needle tip to the target point
    // Rotate needle frame so that the target is placed at the y-z plane of the needle frame to enable the calculation of the
    // curvature.
    Eigen::Matrix4d rotated_needle_frame = bicycle_kinematics.RotateAboutZ(needle_pose_rbt_frame, theta_d);
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
    double w_hat{0};
     // Calculate theta in needle frame and convert theta to a value between 0 and 2*PI
    double needle_theta = fmod(fabs(get_theta(rbt_theta_rad)), 2 * M_PI);
    // Determine normalized rotation velocity
    if (needle_theta - theta_d > M_PI)
    {
        w_hat = 1 - alpha * exp(-pow((2 * M_PI) - (needle_theta - theta_d), 2) / (2 * pow(c, 2)));
    }
    else
    {
        w_hat = 1 - alpha * exp(-pow(needle_theta - theta_d, 2) / (2 * pow(c, 2)));
    }
    // Return converted rotation velocity
    return w_hat;
}

/*!
    This function calculates the desired angular velocity given current needle rotation angle (rad) based on the bidirectional curv steering method.
    Returns: rotational angular velocity in (rad/s)
*/
double CurvSteering::BidirectionalCurv(const double &rbt_theta_rad)
{
    double w_hat{0};
    double needle_theta = get_theta(rbt_theta_rad);
    // Check if it is time to change the direction of rotation
    if (needle_theta > 2 * M_PI)
    {
        if (current_rotation_dir == RotationDirection::CW)
        {
            current_rotation_dir = RotationDirection::CCW;
        }
    }
    else if (needle_theta < 0)
    {
        if (current_rotation_dir == RotationDirection::CCW)
        {
            current_rotation_dir = RotationDirection::CW;
        }
    }

    // Determine normalized rotation velocity
    if (needle_theta - theta_d > M_PI)
    {
        w_hat = 1 - alpha * exp(-pow((2 * M_PI) - (needle_theta - theta_d), 2) / (2 * pow(c, 2)));
    }
    else
    {
        w_hat = 1 - alpha * exp(-pow(needle_theta - theta_d, 2) / (2 * pow(c, 2)));
    }
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