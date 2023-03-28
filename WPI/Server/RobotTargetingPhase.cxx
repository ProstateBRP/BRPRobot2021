/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotTargetingPhase.h"
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

RobotTargetingPhase::RobotTargetingPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

RobotTargetingPhase::~RobotTargetingPhase()
{
}

void RobotTargetingPhase::OnExit()
{
  RStatus->robot->StopRobot();
  // Check if the robot has reached its targeting position And if the state is changing to Move to Target
  if (RStatus->robot->isInTargetingPos() && strcmp("MOVE_TO_TARGET", GetNextWorkPhase().c_str()) == 0)
  {
    // Capture the last reported needle tip position
    RStatus->robot->SaveNeedleTipPose();
  }
}

int RobotTargetingPhase::Initialize()
{

  // Send Status after waiting for 2 seconds (mimicking initialization process)
  igtl::Sleep(1000); // wait for 1000 msec
  // If the robot has not been calibrated, return device-not-ready error
  igtl::Matrix4x4 cmatrix;
  if (!this->RStatus || !this->RStatus->GetCalibrationMatrix(cmatrix))
  {
    std::cerr << "ERROR: Attempting to start TARGETING without calibration." << std::endl;
    this->SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_NOT_READY, 0);
  }
  else
  {
    // Enable the axis to move
    RStatus->robot->EnableMove();
    this->SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
  }

  return 1;
}

int RobotTargetingPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{

  if (RobotPhaseBase::MessageHandler(headerMsg))
  {
    return 1;
  }

  /// Check if GET_TRANSFORM has been received
  if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0 &&
      strncmp(headerMsg->GetDeviceName(), "TGT_", 4) == 0)
  {
    igtl::Matrix4x4 matrix;
    this->ReceiveTransform(headerMsg, matrix);
    if (ValidateMatrix(matrix))
    {
      this->RStatus->SetTargetMatrix(matrix);
      std::string devName = headerMsg->GetDeviceName();
      std::stringstream ss;
      ss << "ACK_" << devName.substr(4, std::string::npos);
      SendTransformMessage(ss.str().c_str(), matrix);
      // Mimic target checking process
      igtl::Sleep(1000);
      SendStatusMessage("TARGET", igtl::StatusMessage::STATUS_OK, 0);
      SendTransformMessage("REACHABLE_TARGET", matrix);
      return 1;
    }
  }

  return 0;
}
