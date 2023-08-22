/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotStopPhase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotStopPhase::RobotStopPhase(Robot *robot) : RobotPhaseBase(robot)
{
}

RobotStopPhase::~RobotStopPhase()
{
}

void RobotStopPhase::OnExit()
{
  SetPreviousWorkPhase();
}

int RobotStopPhase::Initialize()
{

  // Send Status after waiting for 2 seconds (mimicking initialization process)
  igtl::Sleep(500); // wait for 1000 msec
  SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);

  return 1;
}

int RobotStopPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  return 0;
}
