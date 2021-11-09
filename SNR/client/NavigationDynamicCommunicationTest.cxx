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

void *NavigationDynamicCommunicationTest::ReceiveFromSlicer(void *ptr)
{
  std::cerr << "---> Starting thread in NavigationDynamicCommunication.cxx to receive messages from Slicer and send to WPI." << std::endl;

  // String arguments:
  std::string currentStringMessage = Global::globalString;
  std::string currentDeviceName = Global::globalDeviceName;

  // Status arguments:
  // std::string currentStatusArgErrorName = Global::globalArgErrorName;
  // std::string currentStatusArgStatusStringMessage = Global::globalArgStatusStringMessage;

  // Transform arguments:
  // TODO

  while(1)
  {
    //std::cout << "Current globalString: " << Global::globalString << std::endl;
    if (currentStringMessage.compare(Global::globalString) != 0 && Global::testRunning == true)
    {
      std::cout << "Sending stringMessage from Slicer to WPI: " << Global::globalString << std::endl;
      currentStringMessage = Global::globalString;
      //std::cout << "Sending new deviceName from Slicer to WPI: Global::globalDeviceName: " << Global::globalDeviceName << std::endl;
      SendStringMessage(Global::globalDeviceName.c_str(), currentStringMessage.c_str());
    }

    // if (currentStatusArgErrorName.compare(Global::globalArgErrorName) != 0 && Global::testRunning == true)
    // {
    //   std::cout << "Sending statusMessage from Slicer to WPI: Global::globalArgStatusStringMessage: " << Global::globalArgStatusStringMessage << std::endl;
    //   currentStatusArgErrorName = Global::globalArgErrorName;
    //   currentStatusArgStatusStringMessage = Global::globalArgStatusStringMessage;
    //   SendStatusMessage((char*)"statusMessage", Global::globalArgCode, Global::globalArgSubcode, (Global::globalArgErrorName).c_str(), (Global::globalArgStatusStringMessage).c_str());
    // }

    // if (currentTransformMessage.compare(Global::globalTransform) != 0 && Global::testRunning == true)
    // {
    //   // TODO
    // }
  }
  return NULL;
}

void *NavigationDynamicCommunicationTest::SendToSlicer(void *ptr)
{
  std::cerr << "---> Starting thread in NavigationDynamicCommunication.cxx to receive messages from WPI and send to Slicer." << std::endl;
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();

  while(1)
  {
    ReceiveMessageHeader(headerMsg, this->TimeoutFalse);
    
    // Incoming message is a stringMessage:
    if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
    {
      // Receive stringMessage from WPI and send to Slicer
      igtl::StringMessage::Pointer stringMsg;
      stringMsg = igtl::StringMessage::New();
      stringMsg->SetMessageHeader(headerMsg);
      stringMsg->AllocatePack();
      bool timeout(false);
      this->Socket->Receive(stringMsg->GetPackBodyPointer(), stringMsg->GetPackBodySize(), timeout);
      int c = stringMsg->Unpack(1);

      CheckAndReceiveStringMessage(headerMsg, (char*)(headerMsg->GetDeviceName()), (char *)(stringMsg->GetString()));
  
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