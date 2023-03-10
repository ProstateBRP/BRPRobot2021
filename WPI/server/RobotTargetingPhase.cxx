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

RobotTargetingPhase::RobotTargetingPhase() : RobotPhaseBase()
{
}

RobotTargetingPhase::~RobotTargetingPhase()
{
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
      // Mimic moving toward the target
      int inc = 10;
      double x_inc = (matrix[0][3] - this->RStatus->robot.current_pose[0][3])/inc;
      double y_inc = (matrix[1][3] - this->RStatus->robot.current_pose[1][3])/inc;
      double z_inc = (matrix[2][3] - this->RStatus->robot.current_pose[2][3])/inc;
      while (!this->RStatus->robot.isApprox(this->RStatus->robot.current_pose, matrix))
      {
        this->RStatus->robot.current_pose[0][3] += x_inc;
        this->RStatus->robot.current_pose[0][3] += y_inc;
        this->RStatus->robot.current_pose[0][3] += z_inc;
      }
      // Robot has reached the targeting position
      RStatus->robot.in_target_position = true;
      //  Inform Slicer that the robot has reached the targeting position
      SendStringMessage("TargetingComplete","Robot is in Targeting Position!");

      return 1;
    }
    
  }

  return 0;
}
