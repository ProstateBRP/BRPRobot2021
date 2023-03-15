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

RobotMoveToTargetPhase::RobotMoveToTargetPhase() : RobotPhaseBase()
{
}

RobotMoveToTargetPhase::~RobotMoveToTargetPhase()
{
}

int RobotMoveToTargetPhase::Initialize()
{
  if (RStatus->GetTargetFlag())
  {
    SendStatusMessage("MOVE_TO_TARGET", igtl::StatusMessage::STATUS_OK, 0);
    SendTransformMessage("CURRENT_POSITION", RStatus->robot.current_pose);
  }
  else
  {
    // If the target has not been received, return error.
    SendStatusMessage("MOVE_TO_TARGET", igtl::StatusMessage::STATUS_CONFIG_ERROR, 0);
  }

  return 1;
}

int RobotMoveToTargetPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{

  // Check the message
  if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0 &&
      strncmp(headerMsg->GetDeviceName(), "RETRACT_NEEDLE", 4) == 0)
  {
    string text;
    ReceiveString(headerMsg, text);
    SendStatusMessage("ACK_RETRACT_NEEDLE", igtl::StatusMessage::STATUS_OK, 0);
    // The dummy robot is now activated
    igtl::Sleep(2000);
    // Send acknowledgment for successful needle retraction.
    SendStatusMessage("RETRACT_NEEDLE", igtl::StatusMessage::STATUS_OK, 0);
    return 1;
  }

  /// Check if new target is reported
  else if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0 &&
           strncmp(headerMsg->GetDeviceName(), "TGT_", 4) == 0)
  {
    igtl::Matrix4x4 matrix;
    this->ReceiveTransform(headerMsg, matrix);

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

  /// Check if the navigation is sending the needle tip pose
  else if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0 &&
           strncmp(headerMsg->GetDeviceName(), "NPOS_", 5) == 0)
  {
    // Create a matrix to store needle pose
    std::string devName = headerMsg->GetDeviceName();
    igtl::Matrix4x4 matrix;
    this->ReceiveTransform(headerMsg, matrix);

    // Acknowledgement
    std::stringstream ss;
    ss << "ACK_" << devName.substr(5, std::string::npos);
    SendTransformMessage(ss.str().c_str(), matrix);

    // Validate the needle transform matrix
    if (ValidateMatrix(matrix))
    {
      Logger &log = Logger::GetInstance();
      log.Log("OpenIGTLink Needle Tip Received and Set in Code.", devName.substr(5, std::string::npos), LOG_LEVEL_INFO, true);
      // needle pose should be saved in a robot variable in the real robot sw.
      SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
    }
    else
    {
      // Incorrect needle pose send status error
      std::cerr << "ERROR: Invalid calibration matrix." << std::endl;
      SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_CONFIG_ERROR, 0);
    }
    return 1;
  }

  return 0;
}
