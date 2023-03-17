#include "Robot.hpp"

Robot::Robot() : x_inc{0}, y_inc{0}
{
    current_pose = Eigen::Matrix4d::Identity();
    target_position = Eigen::Matrix4d::Identity();
    calibration = Eigen::Matrix4d::Identity();
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
    if (abs(current_pose(0, 3) - target_position(0, 3)) > epsilon || abs(current_pose(1, 3) - target_position(1, 3)) > epsilon)
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
    return 0;
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
