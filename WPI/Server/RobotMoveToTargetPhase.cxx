/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotMoveToTargetPhase.h"
#include <string.h>
#include <stdlib.h>
#include <string>
#include <sstream>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotMoveToTargetPhase::RobotMoveToTargetPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

RobotMoveToTargetPhase::~RobotMoveToTargetPhase()
{
}

int RobotMoveToTargetPhase::Initialize()
{
  if (RStatus->robot->GetInTargetPosFlag())
  {
    SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);

    // If we did not transition from a Stop state, initialize kinematic tip estimation.
    if (strcmp(GetPreviousWorkPhase().c_str(), "STOP") != 0)
    {
      // Send the current kinematic tip position as the first actual tip position
      RStatus->PushBackKinematicTipAsActualPose();
      // Calculate Steering Effort
      RStatus->robot->UpdateCurvParams();
    }
    // Enable the axis to move
    RStatus->robot->EnableMove();
  }
  else
  {
    // Robot is not in the targeting position
    SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_NOT_READY, 0);
  }
  // Send current needle pose to Slicer
  igtl::Matrix4x4 curr_pose;
  RStatus->GetCurrentPosition(curr_pose);
  SendTransformMessage("CURRENT_POSITION", curr_pose);
  return 1;
}

void RobotMoveToTargetPhase::OnExit()
{
  RStatus->robot->StopRobot();
  // Clean up the reported tip positions from the buffer (Skip process if robot is Stopped).
  if (strcmp("STOP", GetNextWorkPhase().c_str()) != 0)
  {
    RStatus->robot->CleanUp();
  }
  SetPreviousWorkPhase();
}

int RobotMoveToTargetPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  // Check the message
  if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
  {
    if (strcmp(headerMsg->GetDeviceName(), "RETRACT_NEEDLE") == 0)
    {
      // Stop robot
      RStatus->robot->StopRobot();
      string text;
      ReceiveString(headerMsg, text);
      SendStatusMessage("ACK_RETRACT_NEEDLE", igtl::StatusMessage::STATUS_OK, 0);
      // Ask the robot to retract the needle
      RStatus->robot->RetractNeedle();
      igtl::Sleep(500); // Simulate the delay

      // Send acknowledgment for successful needle retraction.
      SendStatusMessage("RETRACT_NEEDLE", igtl::StatusMessage::STATUS_OK, 0);
      return 1;
    }
  }

  // Check transform types
  else if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
  {
    /// Check if new target is reported
    if (strncmp(headerMsg->GetDeviceName(), "TGT_", 4) == 0)
    {
      igtl::Matrix4x4 matrix;
      this->ReceiveTransform(headerMsg, matrix);

      this->RStatus->SetTargetMatrix(matrix);

      std::string devName = headerMsg->GetDeviceName();
      std::stringstream ss;
      ss << "ACK_" << devName.substr(4, std::string::npos);
      SendTransformMessage(ss.str().c_str(), matrix);

      // Update target and steering parameters
      RStatus->robot->UpdateCurvParams();

      // Send a status after checking the validity fo the received target, if the target is not reachable by the steering
      // algorithm sends a config error status and sets the steering to max curvature towards the target.
      SendStatusMessage("TARGET", igtl::StatusMessage::STATUS_OK, 0);
      SendTransformMessage("REACHABLE_TARGET", matrix);
      Logger &log = Logger::GetInstance();
      log.Log(matrix, "New Target", devName.substr(4, std::string::npos), 1);

      return 1;
    }
    // Check if the navigation is sending the needle tip position
    else if (strncmp(headerMsg->GetDeviceName(), "NPOS_", 5) == 0)
    {
      // Create a matrix to store needle pose
      std::string devName = headerMsg->GetDeviceName();
      igtl::Matrix4x4 matrix;
      this->ReceiveTransform(headerMsg, matrix);

      // Acknowledgement
      std::stringstream ss;
      ss << "ACK_" << devName.substr(5, std::string::npos);
      SendTransformMessage(ss.str().c_str(), matrix);
      // Stop the robot thread and wait for 200 millisecond for the thread to sync
      RStatus->robot->StopRobot();
      Logger &log = Logger::GetInstance();
      log.Log("OpenIGTLink Needle Tip Received and Set in Code.", devName.substr(5, std::string::npos), LOG_LEVEL_INFO, true);
      log.Log(matrix, "Needle Position", devName.substr(4, std::string::npos), 1);
      // Pushback the reported needle tip position and update the CURV
      RStatus->PushBackActualNeedlePos(matrix);
      // Re-enable the robot
      RStatus->robot->EnableMove();
      // needle pose should be saved in a robot variable in the real robot sw.
      SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
      return 1;
    }
  }
  return 0;
}
