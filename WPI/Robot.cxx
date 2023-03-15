#include "Robot.hpp"

Robot::Robot()
{
    igtl::IdentityMatrix(current_pose);
    igtl::IdentityMatrix(target_position);
    igtl::IdentityMatrix(calibration);
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

int Robot::MoveToTargetingPosition(int increment)
{
    // Calculate the increments in each axis
    double x_inc = (target_position[0][3] - current_pose[0][3]) / increment;
    double y_inc = (target_position[1][3] - current_pose[1][3]) / increment;
    double z_inc = (target_position[2][3] - current_pose[2][3]) / increment;
    
    // Start moving toward the desired target
    while (!isApprox(current_pose, target_position))
    {
        current_pose[0][3] += x_inc;
        current_pose[1][3] += y_inc;
        current_pose[2][3] += z_inc;
        igtl::Sleep(10);
    }
    in_target_position = true;
}

int Robot::InsertNeedleToTargetDepth(int increment)
{
    

}

void Robot::ZeroRobot()
{
    igtl::IdentityMatrix(current_pose);
}