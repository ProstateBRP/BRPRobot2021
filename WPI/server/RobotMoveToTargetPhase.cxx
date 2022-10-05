/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotMoveToTargetPhase.h"
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

RobotMoveToTargetPhase::RobotMoveToTargetPhase() : RobotPhaseBase()
{
}

RobotMoveToTargetPhase::~RobotMoveToTargetPhase()
{
}

int RobotMoveToTargetPhase::Initialize()
{
  if (RStatus->GetTargetFlag())
  {
    // Create a dummy 4x4 matrix to replicate the current pose of the robot and send to Slicer.
    igtl::Matrix4x4 matrix;
    igtl::IdentityMatrix(matrix);
    matrix[0][3] = rand() % 100;
    matrix[1][3] = rand() % 100;
    matrix[2][3] = rand() % 100;
    SendStatusMessage("MOVE_TO_TARGET", igtl::StatusMessage::STATUS_OK, 0);
    SendTransformMessage("CURRENT_POSITION", matrix);
  }
  else
  {
    // Create a dummy 4x4 matrix to replicate the current pose of the robot and send to Slicer.
    igtl::Matrix4x4 matrix;
    igtl::IdentityMatrix(matrix);
    matrix[0][3] = rand() % 100;
    matrix[1][3] = rand() % 100;
    matrix[2][3] = rand() % 100;

    // If the target has not been received, return error.
    SendStatusMessage("MOVE_TO_TARGET", igtl::StatusMessage::STATUS_NOT_READY, 0);
    SendTransformMessage("CURRENT_POSITION", matrix);
  }

  return 1;
}

int RobotMoveToTargetPhase::MessageHandler(igtl::MessageHeader *headerMsg)
{

  if (RobotPhaseBase::MessageHandler(headerMsg))
  {
    return 1;
  }

  return 0;
}
