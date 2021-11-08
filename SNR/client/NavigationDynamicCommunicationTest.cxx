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

#include "NavigationDynamicCommunicationTest.h"
#include "script.hxx"
#include "pthread.h"
#include "chrono"
#include "thread"


NavigationDynamicCommunicationTest::NavigationDynamicCommunicationTest()
{
}

NavigationDynamicCommunicationTest::~NavigationDynamicCommunicationTest()
{
}

// NEW??
void *NavigationDynamicCommunicationTest::ReceiveFromSlicer(void *ptr)
{
  std::cerr << "---> Starting thread to receive messages from Slicer and send to WPI." << std::endl;
  std::cout << "Current global stringMessage: " << Global::globalString << std::endl;
  std::cout << "Current global stringEncoding: " << Global::globalEncoding << std::endl;
  std::string currentStringMessage = Global::globalString;
  std::string currentStringEncoding = Global::globalEncoding;
  
  while(1)
  {
    if (currentStringMessage.compare(Global::globalString) != 0)
    {
      std::cout << "Sending stringMessage from Slicer to WPI: Global::globalString: " << Global::globalString << "; Global::globalEncoding: " << Global::globalEncoding << std::endl;
      currentStringMessage = Global::globalString;
      currentStringEncoding = Global::globalEncoding;
      SendStringMessage(currentStringEncoding.c_str(), currentStringMessage.c_str());
      //SendStringMessage((char *)"CMD_0001", (char*)"START_UP");
    }

    // if (currentStatusMessage.compare(Global::globalStatus) != 0)
    // {
    //   // TODO
    // }

    // if (currentTransformMessage.compare(Global::globalTransform) != 0)
    // {
    //   // TODO
    // }
  }
  return NULL;
}

void *NavigationDynamicCommunicationTest::SendToSlicer(void *ptr)
{
  std::cerr << "---> Starting thread to receive messages from WPI and send to Slicer." << std::endl;
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();

  while(1)
  {
    ReceiveMessageHeader(headerMsg, this->TimeoutFalse);
    
    // Incoming message is a stringMessage:
    if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
    {
      igtl::StringMessage::Pointer stringMsg;
      stringMsg = igtl::StringMessage::New();
      stringMsg->SetMessageHeader(headerMsg);
      stringMsg->AllocatePack();
      // Receive stringMessage from WPI and send to Slicer
      CheckAndReceiveStringMessage(headerMsg, headerMsg->GetDeviceName(), (char *)(stringMsg->GetString()));
    }

    // Incoming message is a statusMessage:
    // TODO

    // Incoming message is a transformMessage:
    // TODO
  }

  return NULL;
}


NavigationDynamicCommunicationTest::ErrorPointType NavigationDynamicCommunicationTest::Test()
{
  int queryCounter = 0;
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();
  
  typedef void *(*THREADFUNCPTR)(void *);
  // Create a thread to receive from Slicer and send to WPI
  pthread_t threadReceive;
  pthread_create(&threadReceive, NULL, (THREADFUNCPTR) &NavigationDynamicCommunicationTest::ReceiveFromSlicer, this);

  // Create a thread to receive from WPI and send to Slicer
  pthread_t threadSend;
  pthread_create(&threadSend, NULL, (THREADFUNCPTR) &NavigationDynamicCommunicationTest::SendToSlicer, this);
  
  // pthread_join(threadReceive, NULL);
  // pthread_join(threadSend, NULL); 

  std::this_thread::sleep_for(std::chrono::seconds(60));
  return SUCCESS;
}