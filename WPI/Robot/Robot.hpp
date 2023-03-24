#pragma once

#include "igtlMath.h"
#include "igtlOSUtil.h"
#include "math.h"
#include "../NeedleKinematics/BicycleKinematics.h"
#include "../SteeringAlgorithm/CurvSteering/CurvSteering.h"
#include "../Utilities/PolynomialFit/PolyFit.h"
#include "Eigen/Dense"
class Robot
{
private:
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
    PolyFit zx_fit;
    PolyFit zy_fit;

protected:
    bool motor_enabled{false};
    bool calibration_received{false};
    bool target_point_received{false};
    Eigen::Matrix4d needle_tip_pose_at_targeting;
    double x_inc;
    double y_inc;
    double delta;
    double max_insertion_speed;
    double max_rotation_speed;
    vector<Eigen::Vector3d> actual_tip_positions;
    double theta{0};
    // ==================== Methods =================================
public:
    Robot();
    ~Robot();
    void UpdateRobot();
    void UpdateCurvParams();
    int MoveToTargetingPosition();
    void CalcMoveToTargetInc(int = 1e3);
    int InsertNeedleToTargetDepth();
    void SetNeedleEntryPoint(const Eigen::Matrix4d &matrix);
    void SaveNeedleTipPose();
    void RetractNeedle();
    void ZeroRobot();
    void StopRobot();
    void EnableMove();
    bool isApprox(const igtl::Matrix4x4 &, const igtl::Matrix4x4 &, double epsilon = 1e-6);
    bool isInTargetingPos(double epsilon = 1e-6);
    bool hasReachedTarget(double epsilon = 1e-2);
    bool isTargetPointReceived() { return target_point_received; }
    bool isCalibrationReceived() { return calibration_received; }
    void SetCalibrationFlag(const bool flag) { calibration_received = flag; };
    void SetTargetPointFlag(const bool flag) { target_point_received = flag; };
    void SetCurrentState(const std::string &state){current_state = state;}
    std::string GetCurrentState(){return current_state;}
    void SetTargetPosition(const Eigen::Matrix4d &);
    void SetCalibration(const Eigen::Matrix4d &);
    Eigen::Matrix4d GetRegistration(){return calibration;}
    Eigen::Matrix4d GetCurrentNeedlePos(){return current_pose;}
    Eigen::Matrix4d GetTargetPointMatrix(){return target_position;}
    Eigen::Vector4d GetTargetPointVector();
    Eigen::Matrix3d CalcActualTipOrientation(const double &, const double &);
    Eigen::Matrix4d CalcActualTipPose(const Eigen::Matrix3d &);
    void PushBackActualNeedlePosAndUpdatePose(const Eigen::Vector3d &);
    void PushBackKinematicTipAsActualPose();
    void CleanUp();
};