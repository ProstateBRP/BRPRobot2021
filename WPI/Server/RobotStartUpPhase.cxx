/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotStartUpPhase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotStartUpPhase::RobotStartUpPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

RobotStartUpPhase::~RobotStartUpPhase()
{
}

void RobotStartUpPhase::OnExit()
{
  SetPreviousWorkPhase();
}

int RobotStartUpPhase::Initialize()
{

  // Send Status after waiting for 0.5 seconds (mimicking initialization process)
  igtl::Sleep(500);
  // Normal
  SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
  return 1;
}

int RobotStartUpPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  return 0;
}
