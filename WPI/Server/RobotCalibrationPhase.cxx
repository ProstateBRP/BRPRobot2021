/*=========================================================================

  Program:   BRP Prostate Robot: Testing  (Client)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#include "RobotCalibrationPhase.h"
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

RobotCalibrationPhase::RobotCalibrationPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

RobotCalibrationPhase::~RobotCalibrationPhase()
{
}

int RobotCalibrationPhase::Initialize()
{
  return 1;
}

void RobotCalibrationPhase::OnExit()
{
  SetPreviousWorkPhase();
}
// TODO: this should return a 4x4 matrix and set the robot registration to it
// The calibration matrix is set within the RStatus object
int RobotCalibrationPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{

  // As of now the MessageHandler in the PhaseBase always returns 0
  if (RobotPhaseBase::MessageHandler(headerMsg))
  {
    return 1;
  }

  /// Check if Transform message for calibration has been received
  if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0 &&
      strncmp(headerMsg->GetDeviceName(), "CLB_", 4) == 0)
  {
    igtl::Matrix4x4 matrix;
    this->ReceiveTransform(headerMsg, matrix);

    // Acknowledgement
    std::string devName = headerMsg->GetDeviceName();
    std::stringstream ss;
    ss << "ACK_" << devName.substr(4, std::string::npos);

    SendTransformMessage(ss.str().c_str(), matrix);

    // Mimic calibration process
    igtl::Sleep(1000);

    if (ValidateMatrix(matrix))
    {
      if (this->RStatus)
      {
        this->RStatus->SetCalibrationMatrix(matrix);
      }
        SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
      Logger &log = Logger::GetInstance();
      log.Log(matrix, this->Name(),devName.substr(4, std::string::npos), 1);
    }
    else
    {
      std::cerr << "ERROR: Invalid calibration matrix." << std::endl;
      SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_CONFIG_ERROR, 0);
    }

    return 1;
  }

  return 0;
}
