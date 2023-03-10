#include "Robot.hpp"

Robot::Robot()
{
    igtl::IdentityMatrix(current_pose);
    igtl::IdentityMatrix(target_position);
    igtl::IdentityMatrix(calibration);
}

bool Robot::isApprox(const igtl::Matrix4x4 &mtx1, const igtl::Matrix4x4 &mtx2, double epsilon)
{
    for (int i=0; i<4 ; i++)
    {
        for (int j = 0; j<4; j++)
        {
            if (abs(mtx1[i][j] - mtx2[i][j]) > epsilon)
            {
                return false;
            }
        }
    }
    return true;
}