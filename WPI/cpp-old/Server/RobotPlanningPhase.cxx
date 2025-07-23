/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotPlanningPhase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotPlanningPhase::RobotPlanningPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

RobotPlanningPhase::~RobotPlanningPhase()
{
}

int RobotPlanningPhase::Initialize()
{
  SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
  return 1;
}

void RobotPlanningPhase::OnExit()
{
  SetPreviousWorkPhase();
}

int RobotPlanningPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  return 0;
}
