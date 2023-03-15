#pragma once
#include "igtlMath.h"
#include "igtlOSUtil.h"
#include "math.h"
#include "NeedleKinematics/BicycleKinematics.h"
#include "SteeringAlgorithm/CurvSteering/CurvSteering.h"
class Robot
{
public:
    Robot();
    // ==================== Attributes ===============================
    // ==================== Bicycle Kinematics =======================
    BicycleKinematics kinematics;
    // ==================== Steering Algorithm =======================
    CurvMethod *curv_method = new CurvMethod(CurvMethod::BIDIRECTIONAL);
	CurvSteering *curv_steering = new CurvSteering(curv_method);
    // ==================== Class attributes =========================
    igtl::Matrix4x4 current_pose;
    igtl::Matrix4x4 target_position;
    igtl::Matrix4x4 calibration;
    bool in_target_position {false}; // flag to indicate whether the robot has reached the initial target and is ready for insertion.
    bool reached_target {false}; // flag to indicate whether the needle has reached the desired target depth.
    bool isApprox(const igtl::Matrix4x4&, const igtl::Matrix4x4 &, double epsilon = 1e-6);
    // ==================== Methods =================================
    int MoveToTargetingPosition(int increment=1e4);
    int InsertNeedleToTargetDepth(int increment=1e4);
    void ZeroRobot();
};