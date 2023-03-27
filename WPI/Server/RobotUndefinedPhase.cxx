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
}
RobotUndefinedPhase::~RobotUndefinedPhase()
{
}

int RobotUndefinedPhase::Initialize()
{
  return 1;
}

int RobotUndefinedPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{

  if (RobotPhaseBase::MessageHandler(headerMsg))
  {
    return 1;
  }

  return 0;
}
