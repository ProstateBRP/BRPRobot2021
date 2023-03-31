#include "Robot.hpp"

Robot::Robot() : x_inc{0}, y_inc{0}, delta{1e-3}, max_insertion_speed{10}, max_rotation_speed{4 * M_PI}, zx_fit{PolyFit("zx")},
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
    for (int i = 0; i < 3; i++)
    {
        for (int j = 0; j < 3; j++)
        {
            if (abs(current_pose(i, j) - target_position(i, j)) > epsilon)
            {
                return false;
            }
        }
    }
    // Check the x and y of the robot
    if ((abs(current_pose(0, 3) - target_position(0, 3)) > epsilon) || (abs(current_pose(1, 3) - target_position(1, 3)) > epsilon))
    {
        return false;
    }
    // The robot has reached the targeting position
    return true;
}

int Robot::MoveToTargetingPosition()
{
    if (!isInTargetingPos() && motor_enabled)
    {
        current_pose.block(0,0,3,3) = target_position.block(0,0,3,3);
        current_pose(0, 3) += x_inc;
        current_pose(1, 3) += y_inc;
        igtl::Sleep(10);
        return 1;
    }
    return 0;
}

void Robot::CalcMoveToTargetInc(int increment)
{
    // Calculate the increments in each axis
    x_inc = (target_position(0, 3) - current_pose(0, 3)) / increment;
    y_inc = (target_position(1, 3) - current_pose(1, 3)) / increment;
}

int Robot::InsertNeedleToTargetDepth()
{
    if (!hasReachedTarget() && motor_enabled)
    {
        std::cerr << "Has not reached target yet!" << std::endl;
        double du1 = max_insertion_speed * delta;
        double w_hat = curv_steering->CalcRotationalVel(theta);
        double du2 = w_hat * max_rotation_speed;
        // Update the needle rotation
        theta += du2;
        current_pose = kinematics.ForwardKinematicsBicycleModel(current_pose, du1, du2);
        igtl::Sleep(10);
        return 1;
    }
    return 0;
}

bool Robot::hasReachedTarget(double epsilon)
{
    return !(abs(current_pose(2, 3) - target_position(2, 3)) > epsilon);
}

void Robot::ZeroRobot()
{
    current_pose.setIdentity();
}

void Robot::StopRobot()
{
    motor_enabled = false;
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
}

void Robot::SetCalibration(const Eigen::Matrix4d &calibration)
{
    this->calibration = calibration;
    this->SetCalibrationFlag(true);
}

void Robot::PushBackActualNeedlePosAndUpdatePose(const Eigen::Vector3d &reported_tip_pos)
{
    actual_tip_positions.push_back(reported_tip_pos);
    zx_fit.Fit(actual_tip_positions);
    zy_fit.Fit(actual_tip_positions);
    // estimate rotation angle about
    double beta = zx_fit.CalcAngle();
    double omega = zy_fit.CalcAngle();
    // Update the current pose based on the estimated pose
    current_pose = kinematics.ApplyRotation(current_pose, Eigen::Vector3d(theta, beta, omega));
}

void Robot::PushBackKinematicTipAsActualPose()
{
    actual_tip_positions.clear();
    actual_tip_positions.push_back(Eigen::Vector3d(current_pose(0,3),current_pose(1,3),current_pose(2,3)));
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
    // TODO:Potentially look into conditional cleanup based on the interrupt level
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
    current_pose.Identity();
    target_position.Identity();
    calibration.Identity();
    calibration_received = false;
    target_point_received = false;
    CleanUp();
}