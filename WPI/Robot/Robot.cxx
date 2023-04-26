#include "Robot.hpp"

Robot::Robot() : x_inc{0}, y_inc{0}, delta{1e-4}, max_insertion_speed{0.5}, max_rotation_speed{4 * M_PI}, zx_fit{PolyFit("zx")},
                 zy_fit{PolyFit("zy")}
{
    current_pose = Eigen::Matrix4d::Identity();
    target_position = Eigen::Matrix4d::Identity();
    calibration = Eigen::Matrix4d::Identity();
}
Robot::~Robot()
{
    delete curv_method;
    delete curv_steering;
}

void Robot::UpdateRobot()
{
    if (current_state == "TARGETING")
    {
        MoveToTargetingPosition();
    }
    else if (current_state == "MOVE_TO_TARGET")
    {
        InsertNeedleToTargetDepth();
    }
}

bool Robot::isApprox(const igtl::Matrix4x4 &mtx1, const igtl::Matrix4x4 &mtx2, double epsilon)
{
    for (int i = 0; i < 4; i++)
    {
        for (int j = 0; j < 4; j++)
        {
            if (abs(mtx1[i][j] - mtx2[i][j]) > epsilon)
            {
                return false;
            }
        }
    }
    return true;
}

bool Robot::isInTargetingPos(double epsilon)
{
    // Check the orientation
    if (current_pose.block(0, 0, 3, 3) != target_position.block(0, 0, 3, 3))
    {
        return false;
    }
    // Check the x and y of the robot
    if ((abs(current_pose(0, 3) - x_goal) > epsilon) || (abs(current_pose(1, 3) - y_goal) > epsilon))
    {
        return false;
    }
    // The robot has reached the targeting position
    return true;
}

int Robot::MoveToTargetingPosition()
{
    if (motor_enabled && !GetInTargetPosFlag())
    {
        if (!isInTargetingPos())
        {
            current_pose.block(0, 0, 3, 3) = target_position.block(0, 0, 3, 3);
            current_pose(0, 3) += x_inc;
            current_pose(1, 3) += y_inc;
            igtl::Sleep(10);
            return 1;
        }
        else
        {
            SetInTargetPosFlag(true);
        }
    }

    return 0;
}

void Robot::CalcMoveToTargetInc(int increment)
{
    // Calculate target's rotation in Euler angles
    Eigen::Vector3d rot_angles = ConvertRotationMatrixToEulerAngles(target_position.block(0, 0, 3, 3));
    double x_prime = target_position(2, 3) * -tan(rot_angles(1));
    double y_prime = target_position(2, 3) * tan(rot_angles(0));
    x_goal = target_position(0, 3) + x_prime;
    y_goal = target_position(1, 3) + y_prime;
    // Calculate the increments in each axis
    x_inc = (x_goal - current_pose(0, 3)) / increment;
    y_inc = (y_goal - current_pose(1, 3)) / increment;
}

int Robot::InsertNeedleToTargetDepth()
{
    if (!hasReachedTarget() && motor_enabled)
    {
        double du1 = max_insertion_speed * delta;
        double w_hat = curv_steering->CalcRotationalVel(theta); // Desired normalized rot speed
        double u2 = w_hat * max_rotation_speed;                 // desired rotation speed
        double du2 = u2 * delta;                                // Change in rotation angle
        // Update the needle rotation
        theta += du2;
        current_pose = kinematics.ForwardKinematicsBicycleModel(current_pose, du1, du2);
        return 1;
    }
    return 0;
}

bool Robot::hasReachedTarget()
{
    return !(current_pose(2, 3) < target_position(2, 3));
}

void Robot::ZeroRobot()
{
    current_pose.setIdentity();
}

void Robot::StopRobot()
{
    motor_enabled = false;
    igtl::Sleep(200);
}
void Robot::EnableMove()
{
    motor_enabled = true;
}

void Robot::SetTargetPosition(const Eigen::Matrix4d &target_position)
{
    this->target_position = target_position;
    this->CalcMoveToTargetInc();
    this->SetTargetPointFlag(true);
    this->SetInTargetPosFlag(false);
}

void Robot::SetCalibration(const Eigen::Matrix4d &calibration)
{
    this->calibration = calibration;
    this->SetCalibrationFlag(true);
}

void Robot::PushBackActualNeedlePosAndUpdatePose(const Eigen::Vector3d &reported_tip_pos)
{
    Logger &log = Logger::GetInstance();
    // Convert reported tip position from robot base to needle guide's frame.
    Eigen::Vector4d reported_tip_pos_needle_guide_coord = needle_tip_pose_at_targeting.inverse() *
                                                          Eigen::Vector4d(reported_tip_pos(0), reported_tip_pos(1), reported_tip_pos(2), 1);
    actual_tip_positions.push_back(Eigen::Vector3d(reported_tip_pos_needle_guide_coord.head(3)));

    zx_fit.Fit(actual_tip_positions);
    zy_fit.Fit(actual_tip_positions);
    // estimate rotation angle about
    double beta = zx_fit.CalcAngle();
    double omega = -zy_fit.CalcAngle();
    // Log estimated rotation angles about the needle base for the needle tip pose
    string ss{"Beta,  " + to_string(beta)};
    log.Log(ss, 1);
    ss.clear();
    ss = "Omega,  " + to_string(omega);
    log.Log(ss, 1);
    ss = "Theta,  " + to_string(theta);
    log.Log(ss, 1);

    // Update the current pose based on the estimated pose
    // Update orientation component of needle tip
    current_pose = kinematics.ApplyRotationFixedAngles(needle_tip_pose_at_targeting, Eigen::Vector3d(omega, beta, theta));
    // Update Position component of needle tip
    current_pose(0, 3) = reported_tip_pos(0);
    current_pose(1, 3) = reported_tip_pos(1);
    current_pose(2, 3) = reported_tip_pos(2);
    UpdateCurvParams();
}

void Robot::PushBackKinematicTipAsActualPose()
{
    actual_tip_positions.clear();
    /* The first point is considered as the needle guide's frame location. Since all preceding points are defined w.r.t needle
    guide's frame, the first point is defined as the base of the needle guide frame and is therefore zeros.*/
    actual_tip_positions.push_back(Eigen::Vector3d::Zero());
}

void Robot::SetNeedleEntryPoint(const Eigen::Matrix4d &matrix)
{
    actual_tip_positions.clear();
    Eigen::Vector3d entry_pt(matrix(0, 3), matrix(1, 3), matrix(2, 3));
    actual_tip_positions.push_back(entry_pt);
}

void Robot::CleanUp()
{
    actual_tip_positions.clear();
}

// Save needle tip position before entering the anatomy
void Robot::SaveNeedleTipPose()
{
    needle_tip_pose_at_targeting = current_pose;
}
// Function to simulate the action of retracting the needle to the outside of anatomy
void Robot::RetractNeedle()
{
    current_pose = needle_tip_pose_at_targeting;
    CleanUp();
    theta = 0;
}
void Robot::UpdateCurvParams()
{
    // const Eigen::Matrix4d &needle_pose_rbt_frame, const Eigen::Vector4d &tgt_pos_rbt_frame, const double &rbt_rot_angle_rad
    curv_steering->CalcCurvParams(current_pose, GetTargetPointVector(), theta);
}

Eigen::Vector4d Robot::GetTargetPointVector()
{
    return Eigen::Vector4d(target_position(0, 3), target_position(1, 3), target_position(2, 3), 1);
}

void Robot::Reset()
{
    current_pose.setIdentity();
    target_position.setIdentity();
    calibration.setIdentity();
    calibration_received = false;
    target_point_received = false;
    x_goal = 0;
    y_goal = 0;
    theta = 0;
    CleanUp();
}

Eigen::Vector3d Robot::ConvertRotationMatrixToEulerAngles(Eigen::Matrix3d rotation_mtx)
{
    Eigen::Vector3d angles;
    angles.setZero();
    if (rotation_mtx(2, 0) != 1 && rotation_mtx(2, 0) != -1)
    {
        double pitch1 = -1 * asin(rotation_mtx(2, 0));
        double pitch2 = M_PI - pitch1;
        double roll1 = atan2(rotation_mtx(2, 1) / cos(pitch1),
                             rotation_mtx(2, 2) / cos(pitch1));
        double roll2 = atan2(rotation_mtx(2, 1) / cos(pitch2),
                             rotation_mtx(2, 2) / cos(pitch2));
        double yaw1 = atan2(rotation_mtx(1, 0) / cos(pitch1), rotation_mtx(0, 0) / cos(pitch1));
        double yaw2 = atan2(rotation_mtx(1, 0) / cos(pitch2), rotation_mtx(0, 0) / cos(pitch2));
        angles << roll1, pitch1, yaw1;
    }
    else
    {
        angles(2) = 0;
        if (rotation_mtx(2, 0) == -1)
        {
            angles(1) = M_PI / 2;
            angles(0) = angles(1) + atan2(rotation_mtx(0, 1), rotation_mtx(0, 2));
        }
        else
        {
            angles(1) = -M_PI / 2;
            angles(0) = -angles(2) + atan2(-rotation_mtx(0, 1), -rotation_mtx(0, 2));
        }
    }
    return angles;
}