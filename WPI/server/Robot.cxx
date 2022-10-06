#include "Robot.hpp"

Robot::Robot()
{
    igtl::IdentityMatrix(current_position);
    igtl::IdentityMatrix(target_position);
    igtl::IdentityMatrix(calibration);
}