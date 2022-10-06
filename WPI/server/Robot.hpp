#pragma once
#include "igtlMath.h"

class Robot
{
public:
    Robot();
    igtl::Matrix4x4 current_position;
    igtl::Matrix4x4 target_position;
    igtl::Matrix4x4 calibration;
};