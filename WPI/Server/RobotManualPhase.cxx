/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotManualPhase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotManualPhase::RobotManualPhase() : RobotPhaseBase()
{
}

RobotManualPhase::~RobotManualPhase()
{
}

int RobotManualPhase::Initialize()
{

  // Send Status after waiting for 2 seconds (mimicking initialization process)
  igtl::Sleep(1000); // wait for 1000 msec
  this->SendStatusMessage(this->Name(), 1, 0);

  return 1;
}

void RobotManualPhase::OnExit()
{
}

// What does this function do exactly? It seems that it is always returning zero.
int RobotManualPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{

  if (RobotPhaseBase::MessageHandler(headerMsg))
  {
    return 1;
  }

  return 0;
}
