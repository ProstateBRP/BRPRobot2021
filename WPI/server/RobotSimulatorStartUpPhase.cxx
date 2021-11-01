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

#include "RobotSimulatorStartUpPhase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotSimulatorStartUpPhase::RobotSimulatorStartUpPhase() :
  RobotSimulatorPhaseBase()
{
  // Register Device-not-ready defect
  this->RegisterDefectType("DNR", "Device-not-ready in START_UP phase.");
}


RobotSimulatorStartUpPhase::~RobotSimulatorStartUpPhase()
{
}

int RobotSimulatorStartUpPhase::Initialize()
{

  // Send Status after waiting for 2 seconds (mimicking initialization process)
  igtl::Sleep(2000); // wait for 2000 msec

  if (this->GetDefectStatus("DNR"))
    {
    // Device-not-ready defect is active
    this->SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_NOT_READY, 0);
    }
  else
    {
    // Normal
    this->SendStatusMessage(this->Name(), 1, 0);
    }

  return 1;
}


int RobotSimulatorStartUpPhase::MessageHandler(igtl::MessageHeader* headerMsg)
{

  if (RobotSimulatorPhaseBase::MessageHandler(headerMsg))
    {
    return 1;
    }

  return 0;
}

