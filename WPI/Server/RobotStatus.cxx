/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotStatus.h"
#include "igtlMath.h"

RobotStatus::RobotStatus(Robot *robot)
{
  this->robot = robot;
}

RobotStatus::~RobotStatus()
{
}

void RobotStatus::SetCalibrationMatrix(igtl::Matrix4x4 &matrix)
{
  // Convert to Eigen
  Eigen::Matrix4d calibration = Eigen::Matrix4d::Identity();
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 4; j++)
    {
      calibration(i, j) = matrix[i][j];
    }
  }
  robot->SetCalibrationFlag(true);
  robot->SetCalibration(calibration);
}

int RobotStatus::GetCalibrationMatrix(igtl::Matrix4x4 &matrix)
{
  if (robot->isCalibrationReceived())
  {
    Eigen::Matrix4d calibration = robot->GetRegistration();
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 4; j++)
      {
        matrix[i][j] = calibration(i, j);
      }
    }
    return 1;
  }
  else
  {
    return 0;
  }
}

void RobotStatus::SetTargetMatrix(igtl::Matrix4x4 &matrix)
{
  // Convert to Eigen matrix
  Eigen::Matrix4d target_in_imager_frame = Eigen::Matrix4d::Identity();
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 4; j++)
    {
      target_in_imager_frame(i, j) = matrix[i][j];
    }
  }
  // Calculate the target point in robot base and set in the robot
  robot->SetTargetPosition(robot->GetRegistration().inverse() * target_in_imager_frame);
}

int RobotStatus::GetTargetMatrix(igtl::Matrix4x4 &matrix)
{
  if (robot->isTargetPointReceived())
  {
    // Convert target to imager frame
    Eigen::Matrix4d target_in_imager_frame = robot->GetRegistration() * robot->GetTargetPointMatrix();
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 4; j++)
      {
        matrix[i][j] = target_in_imager_frame(i, j);
      }
    }
    return 1;
  }
  else
  {
    return 0;
  }
}

/*!
Returns current tip pose of the robot in imager frame.
*/
void RobotStatus::GetCurrentPosition(igtl::Matrix4x4 &matrix)
{
  // Convert to imager frame
  Eigen::Matrix4d current_pose_in_imager_frame = robot->GetRegistration() * robot->GetCurrentNeedlePos();
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 4; j++)
    {
      matrix[i][j] = current_pose_in_imager_frame(i, j);
    }
  }
}

void RobotStatus::PushBackActualNeedlePos(const igtl::Matrix4x4 &matrix)
{
  // Convert to Eigen matrix
  Eigen::Matrix4d reported_needle_pos_imager = Eigen::Matrix4d::Identity();
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 4; j++)
    {
      reported_needle_pos_imager(i, j) = matrix[i][j];
    }
  }
  Eigen::Matrix4d reported_needle_tip_robot = robot->GetRegistration().inverse() * reported_needle_pos_imager;
  Eigen::Vector3d needle_tip_pos(reported_needle_tip_robot(0, 3), reported_needle_tip_robot(1, 3),
                                 reported_needle_tip_robot(2, 3));
  this->robot->PushBackActualNeedlePosAndUpdatePose(needle_tip_pos);
}

void RobotStatus::PushBackKinematicTipPose()
{
  robot->PushBackKinematicTipAsActualPose();
}
