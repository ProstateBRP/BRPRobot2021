#pragma once
#include "igtlMath.h"
#include "igtlOSUtil.h"
#include "math.h"
#include "NeedleKinematics/BicycleKinematics.h"
#include "SteeringAlgorithm/CurvSteering/CurvSteering.h"
#include "Eigen/Dense"
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
    Eigen::Matrix4d current_pose;
    Eigen::Matrix4d target_position;
    Eigen::Matrix4d calibration;
    string current_state{""};

protected:
    bool *move_interrupted{nullptr};
    bool calibration_received{false};
    bool target_point_received{false};
    double x_inc;
    double y_inc;
    // ==================== Methods =================================
public:
    void UpdateRobot();
    int MoveToTargetingPosition();
    void CalcMoveToTargetInc(int = 1e4);
    int InsertNeedleToTargetDepth();
    void ZeroRobot();
    void StopRobot();
    void EnableMove();
    bool isApprox(const igtl::Matrix4x4 &, const igtl::Matrix4x4 &, double epsilon = 1e-6);
    bool isInTargetingPos(double epsilon = 1e-6);
    bool isTargetPointReceived() { return target_point_received; }
    bool isCalibrationReceived() { return calibration_received; }
    void SetCalibrationFlag(const bool flag) { calibration_received = flag; };
    void SetTargetPointFlag(const bool flag) { target_point_received = flag; };
    void SetTargetPosition(const Eigen::Matrix4d&);
    void SetCalibration(const Eigen::Matrix4d&);
};