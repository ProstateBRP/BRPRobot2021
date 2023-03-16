/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotStatus.h"
#include "igtlMath.h"

RobotStatus::RobotStatus()
{
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
      calibration(i,j) = matrix[i][j];
    }
  }
  this->robot.SetCalibration(calibration);
}

int RobotStatus::GetCalibrationMatrix(igtl::Matrix4x4 &matrix)
{
  if (this->robot.isCalibrationReceived())
  {
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 4; j++)
      {
        matrix[i][j] = this->robot.calibration(i,j);
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
      target_in_imager_frame(i,j) = matrix[i][j];
    }
  }
  // Calculate the target point in robot base and set in the robot
  this->robot.SetTargetPosition(robot.calibration.inverse() * target_in_imager_frame);
}

int RobotStatus::GetTargetMatrix(igtl::Matrix4x4 &matrix)
{
  if (this->robot.isTargetPointReceived())
  {
    // Convert target to imager frame
    Eigen::Matrix4d target_in_imager_frame = this->robot.calibration * this->robot.target_position;
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 4; j++)
      {
        matrix[i][j] = target_in_imager_frame(i,j);
      }
    }
    return 1;
  }
  else
  {
    return 0;
  }
}

void RobotStatus::SetCurrentNeedlePos(const igtl::Matrix4x4 &matrix)
{
  // Convert to Eigen matrix
  Eigen::Matrix4d current_pos_imager = Eigen::Matrix4d::Identity(); 
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 4; j++)
    {
      current_pos_imager(i,j) = matrix[i][j];
    }
  }
  // Convert to robot coordinate frame
  this->robot.current_pose = robot.calibration.inverse() * current_pos_imager;
}

/*!
Returns current tip pose of the robot in imager frame.
*/
void RobotStatus::GetCurrentPosition(igtl::Matrix4x4 &matrix)
{
  // Convert to imager frame
  Eigen::Matrix4d current_pose_in_imager_frame = this->robot.calibration * this->robot.current_pose;
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 4; j++)
    {
      matrix[i][j] = current_pose_in_imager_frame(i, j);
    }
  }
}
