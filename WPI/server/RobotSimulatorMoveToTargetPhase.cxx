/*=========================================================================

  Program:   BRP Prostate Robot: Testing Simulator (Client)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#include "RobotSimulatorMoveToTargetPhase.h"
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

RobotSimulatorMoveToTargetPhase::RobotSimulatorMoveToTargetPhase() :
  RobotSimulatorPhaseBase()
{
}


RobotSimulatorMoveToTargetPhase::~RobotSimulatorMoveToTargetPhase()
{
}

int RobotSimulatorMoveToTargetPhase::Initialize()
{

  igtl::Matrix4x4 matrix;

  // TODO: Check if the robot is ready for move to target
  // Currently it check if a target has been set.
  if (this->RStatus&&!this->RStatus->GetTargetMatrix(matrix))
    {
    igtl::Matrix4x4 matrix;
    
    // If the target has not been received, return error.
    SendStatusMessage("MOVE_TO_TARGET", igtl::StatusMessage::STATUS_NOT_READY, 0);
    SendTransformMessage("CURRENT_POSITION", matrix);
    }
  else
    {
    igtl::Matrix4x4 matrix;
    // Mimic actuator movement
    for (int i = 0; i < 10; i ++)
      {
      SendTransformMessage("CURRENT_POSITION", matrix);
      igtl::Sleep(100);

      // Need to check STOP/EMERGENCY commands.
      }
    
    // Notify that the actuator reaches to the target.
    SendStatusMessage("MOVE_TO_TARGET", igtl::StatusMessage::STATUS_OK, 0);
    SendTransformMessage("CURRENT_POSITION", matrix);
    }
  
  return 1;

}


int RobotSimulatorMoveToTargetPhase::MessageHandler(igtl::MessageHeader* headerMsg)
{

  if (RobotSimulatorPhaseBase::MessageHandler(headerMsg))
    {
    return 1;
    }
  
  

  return 0;
}


