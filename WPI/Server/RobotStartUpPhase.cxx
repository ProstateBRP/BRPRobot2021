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

RobotStartUpPhase::RobotStartUpPhase() : RobotPhaseBase()
{
}

RobotStartUpPhase::~RobotStartUpPhase()
{
}

void RobotStartUpPhase::OnExit()
{
}

int RobotStartUpPhase::Initialize()
{

  // Send Status after waiting for 2 seconds (mimicking initialization process)
  igtl::Sleep(2000); // wait for 2000 msec

  // Normal
  this->SendStatusMessage(this->Name(), 1, 0);

  return 1;
}

int RobotStartUpPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  // In the startup the actual needle tip pose can be initialized (ONLY for the SIMULATION)
  /// Check if the navigation is sending the needle tip pose
  if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0 &&
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
    // Update current needle position
    RStatus->SetCurrentNeedlePos(matrix);
    Logger &log = Logger::GetInstance();
    log.Log("OpenIGTLink Needle Tip Received and Set in Code.", devName.substr(5, std::string::npos), LOG_LEVEL_INFO, true);
    // needle pose should be saved in a robot variable in the real robot sw.
    SendStatusMessage(this->Name(), igtl::StatusMessage::STATUS_OK, 0);
    return 1;
  }

  return 0;
}
