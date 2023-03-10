#pragma once
#include "igtlMath.h"
#include "math.h"

class Robot
{
public:
    Robot();
    igtl::Matrix4x4 current_pose;
    igtl::Matrix4x4 target_position;
    igtl::Matrix4x4 calibration;
    bool in_target_position {false}; // flag to indicate whether the robot has reached the initial target and is ready for insertion.
    bool reached_target {false}; // flag to indicate whether the needle has reached the desired target depth.
    bool isApprox(const igtl::Matrix4x4&, const igtl::Matrix4x4 &, double epsilon = 1e-6);
};