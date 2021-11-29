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

#include "NavigationStartUpErrorTest.h"


NavigationStartUpErrorTest::NavigationStartUpErrorTest()
{
}

NavigationStartUpErrorTest::~NavigationStartUpErrorTest()
{
}

NavigationStartUpErrorTest::ErrorPointType NavigationStartUpErrorTest::Test()
{
  int queryCounter = 0;
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();

  std::cerr << std::endl;
  std::cerr << "+-------------------- Instruction --------------------+" << std::endl;
  std::cerr << "|                                                     |" << std::endl;
  std::cerr << "|    Remove the hardware from the control computer.   |" << std::endl;
  std::cerr << "|          Please press any key if ready...           |" << std::endl;
  std::cerr << "|                                                     |" << std::endl;
  std::cerr << "+-----------------------------------------------------+" << std::endl;
  std::cin.get();

  std::cerr << "MESSAGE: ===== Step 1: START_UP =====" << std::endl;
  SendStringMessage("CMD_0001", "START_UP");
  ReceiveMessageHeader(headerMsg, this->TimeoutShort);
  if (!CheckAndReceiveStringMessage(headerMsg, "ACK_0001", "START_UP")) return Error(1,1);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "CURRENT_STATUS", 1, 0, "START_UP")) return Error(1,2);
  ReceiveMessageHeader(headerMsg, this->TimeoutLong);
  if (!CheckAndReceiveStatusMessage(headerMsg, "START_UP", igtl::StatusMessage::STATUS_NOT_READY)) return Error(1,3);

  return SUCCESS;
}
