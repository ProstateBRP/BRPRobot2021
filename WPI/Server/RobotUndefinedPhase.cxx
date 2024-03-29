/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotUndefinedPhase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotUndefinedPhase::RobotUndefinedPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

void RobotUndefinedPhase::OnExit()
{
  SetPreviousWorkPhase();
}
RobotUndefinedPhase::~RobotUndefinedPhase()
{
}

int RobotUndefinedPhase::Initialize()
{
  SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
  return 1;
}

int RobotUndefinedPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  return 0;
}
