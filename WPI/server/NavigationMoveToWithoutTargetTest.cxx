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

#include <string.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"

#include "NavigationMoveToWithoutTargetTest.h"


NavigationMoveToWithoutTargetTest::NavigationMoveToWithoutTargetTest()
{
}

NavigationMoveToWithoutTargetTest::~NavigationMoveToWithoutTargetTest()
{
}

NavigationMoveToWithoutTargetTest::ErrorPointType NavigationMoveToWithoutTargetTest::Test()
{
  int queryCounter = 0;
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();

  std::cerr << "MESSAGE: ===== Step 1: START_UP =====" << std::endl;
  SendStringMessage("CMD_0001", "START_UP");
  ReceiveMessageHeader(headerMsg, this->TimeoutShort);
  if (!CheckAndReceiveStringMessage(headerMsg, "ACK_0001", "START_UP")) return Error(1,1);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CURRENT_STATUS", 1, 0, "START_UP")) return Error(1,2);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "START_UP", 1)) return Error(1,3);

  std::cerr << "MESSAGE: ===== Step 2: PLANNING =====" << std::endl;
  SendStringMessage("CMD_0002", "PLANNING");
  ReceiveMessageHeader(headerMsg, this->TimeoutMedium);
  if (!CheckAndReceiveStringMessage(headerMsg, "ACK_0002", "PLANNING")) return Error(2,1);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CURRENT_STATUS", 1, 0, "PLANNING")) return Error(2,2);
  
  std::cerr << "MESSAGE: ===== Step 3: CALIBRATION =====" << std::endl;
  SendStringMessage("CMD_0003", "CALIBRATION");
  ReceiveMessageHeader(headerMsg, this->TimeoutMedium);
  if (!CheckAndReceiveStringMessage(headerMsg, "ACK_0003", "CALIBRATION")) return Error(3,1);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CURRENT_STATUS", 1, 0, "CALIBRATION")) return Error(3,2);

  igtl::Matrix4x4 matrix;
  //GetRandomTestMatrix(matrix);
  igtl::IdentityMatrix(matrix);
  SendTransformMessage("CLB_0004", matrix);
  ReceiveMessageHeader(headerMsg, this->TimeoutMedium);
  if (!CheckAndReceiveTransformMessage(headerMsg, "ACK_0004", matrix)) return Error(3,3);
  // TODO: How can we differenciate Error(3,2) and Error(3,3)?
  
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CALIBRATION", 1)) return Error(3,5);

  std::cerr << "MESSAGE: ===== Step 4: TARGETING =====" << std::endl;
  SendStringMessage("CMD_0005", "TARGETING");
  ReceiveMessageHeader(headerMsg, this->TimeoutMedium);
  if (!CheckAndReceiveStringMessage(headerMsg, "ACK_0005", "TARGETING")) return Error(4,1);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CURRENT_STATUS", 1, 0, "TARGETING")) return Error(4,2);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "TARGETING", 1)) return Error(4,3);

  std::cerr << "MESSAGE: ===== Step 5: MOVE_TO_TARGET =====" << std::endl;
  SendStringMessage("CMD_0007", "MOVE_TO_TARGET");
  ReceiveMessageHeader(headerMsg, this->TimeoutMedium);
  if (!CheckAndReceiveStringMessage(headerMsg, "ACK_0007", "MOVE_TO_TARGET")) return Error(5,1);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CURRENT_STATUS", 1, 0, "MOVE_TO_TARGET")) return Error(5,2);
  ReceiveMessageHeader(headerMsg, this->TimeoutMedium);
  if (!CheckAndReceiveStatusMessage(headerMsg, "MOVE_TO_TARGET", igtl::StatusMessage::STATUS_NOT_READY)) return Error(5,3);

  return SUCCESS;
}
