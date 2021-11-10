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

//void *NavigationDynamicCommunicationTest::ReceiveFromSlicer(void *ptr)
void *NavigationDynamicCommunicationTest::ReceiveFromSlicer()
{
  std::cerr << "---> Starting thread in NavigationDynamicCommunication.cxx to receive messages from Slicer and send to WPI.\n" << std::endl;

  // String arguments:
  std::string currentStringMessage = Global::globalString;
  std::string currentDeviceName = Global::globalDeviceName;

  // Status arguments:
  int currentStatusArgCode = Global::globalArgCode;
  int currentStatusArgSubCode = Global::globalArgSubcode;
  std::string currentStatusArgErrorName = Global::globalArgErrorName;
  std::string currentStatusArgStatusStringMessage = Global::globalArgStatusStringMessage;
  
  // Transform arguments:
  igtl::Matrix4x4 currentMatrix = {{0,0,0,0},
                                  {0,0,0,0},
                                  {0,0,0,0},
                                  {0,0,0,0}};

  while(1)
  {
    // New stringMessage from Slicer
    if (currentStringMessage.compare(Global::globalString) != 0 && Global::testRunning == true)
    {
      std::cout << "Sending stringMessage from Slicer to WPI: " << Global::globalString << std::endl;
      currentStringMessage = Global::globalString;
      SendStringMessage(Global::globalDeviceName.c_str(), currentStringMessage.c_str());
    }

    // New statusMessage from Slicer
    if (currentStatusArgErrorName.compare(Global::globalArgErrorName) != 0 || 
      currentStatusArgStatusStringMessage.compare(Global::globalArgStatusStringMessage) != 0 ||
      currentStatusArgCode != Global::globalArgCode ||
      currentStatusArgSubCode != Global::globalArgSubcode)
    {
      if (Global::testRunning == true && Global::globalArgSubcode != 2687068) // If currentStatusArgSubCode == 2687068, then the message is Slicer's status that gets sent on start up. Remove this from the if statement in the future.
      {
        std::cout << "Sending statusMessage from Slicer to WPI: " << Global::globalArgStatusStringMessage << std::endl;
        currentStatusArgCode = Global::globalArgCode;
        currentStatusArgSubCode = Global::globalArgSubcode;
        currentStatusArgErrorName = Global::globalArgErrorName;
        currentStatusArgStatusStringMessage = Global::globalArgStatusStringMessage;
        SendStatusMessage(Global::globalDeviceName.c_str(), currentStatusArgCode, currentStatusArgSubCode, (currentStatusArgErrorName).c_str(), (currentStatusArgStatusStringMessage).c_str());
        //SendStatusMessage((char*)"CMD_0001", 10, 101010, (char *)"errorName", (char*)"errorStringMessage");

        std::cerr << "========== STATUS ==========" << std::endl;
        std::cerr << " Code      : " << Global::globalArgCode << std::endl;
        std::cerr << " SubCode   : " << Global::globalArgSubcode << std::endl;
        std::cerr << " Error Name: " << Global::globalArgErrorName << std::endl;
        std::cerr << " Status    : " << Global::globalArgStatusStringMessage << std::endl;
        std::cerr << "============================" << std::endl
                  << std::endl;
      }
    }

    // New transformMessage from Slicer
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 4; j++)
      {
        if (currentMatrix[i][j] != Global::globalMatrix[i][j] && Global::testRunning == true)
        {
          std::cout << "Sending transformMessage from Slicer to WPI: " << std::endl;
          memcpy(currentMatrix, Global::globalMatrix, sizeof(Global::globalMatrix));
          igtl::PrintMatrix(currentMatrix);
          SendTransformMessage(Global::globalDeviceName.c_str(), currentMatrix);
        }
      }
    }
  }
  return NULL;
}

// void *NavigationDynamicCommunicationTest::SendToSlicer(void *ptr)
void *NavigationDynamicCommunicationTest::SendToSlicer()
{
  std::cerr << "---> Starting thread in NavigationDynamicCommunication.cxx to receive messages from WPI and send to Slicer." << std::endl;
  // igtl::MessageHeader::Pointer headerMsg;
  // headerMsg = igtl::MessageHeader::New();

  while(1)
  {
    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();
    ReceiveMessageHeader(headerMsg, this->TimeoutFalse);
    
    // Incoming message is a stringMessage:
    if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
    {
      std::cout << "new string sent from wpi to send to slicer!" << std::endl;
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
    if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
    {
      std::cout << "new status sent from wpi to send to slicer!" << std::endl;
      // Receive statusMessage from WPI and send to Slicer
      igtl::StatusMessage::Pointer statusMsg;
      statusMsg = igtl::StatusMessage::New();
      statusMsg->SetMessageHeader(headerMsg);
      statusMsg->AllocatePack();

      bool timeout(false);
      this->Socket->Receive(statusMsg->GetPackBodyPointer(), statusMsg->GetPackBodySize(), timeout);
      int c = statusMsg->Unpack(1);

      // WHAT IS SUFFIX ARGUMENT?
      int suffix = 1;

      CheckAndReceiveStatusMessage(headerMsg, (char*)(headerMsg->GetDeviceName()), statusMsg->GetCode(), suffix, statusMsg->GetErrorName());
    }

    // Incoming message is a transformMessage:
    if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
    {
      std::cout << "new transform sent from wpi to send to slicer!" << std::endl;
      // Receive transformMessage from WPI and send to Slicer
      igtl::TransformMessage::Pointer transMsg;
      transMsg = igtl::TransformMessage::New();
      transMsg->SetMessageHeader(headerMsg);
      transMsg->AllocatePack();

      // Receive transform data from the socket
      bool timeout(false);
      this->Socket->Receive(transMsg->GetPackBodyPointer(), transMsg->GetPackBodySize(), timeout);
      int c = transMsg->Unpack(1);
      igtl::Matrix4x4 matrix;
      transMsg->GetMatrix(matrix);

      CheckAndReceiveTransformMessage(headerMsg, (char*)(headerMsg->GetDeviceName()), matrix);
    }

  }

  return NULL;
}


NavigationDynamicCommunicationTest::ErrorPointType NavigationDynamicCommunicationTest::Test()
{
  int queryCounter = 0;
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();
  
  // typedef void *(*THREADFUNCPTR)(void *);
  // // Create a thread to receive from Slicer and send to WPI
  // pthread_t threadReceive;
  // pthread_create(&threadReceive, NULL, (THREADFUNCPTR) &NavigationDynamicCommunicationTest::ReceiveFromSlicer, this);

  // // Create a thread to receive from WPI and send to Slicer
  // pthread_t threadSend;
  // pthread_create(&threadSend, NULL, (THREADFUNCPTR) &NavigationDynamicCommunicationTest::SendToSlicer, this);
  
  // // pthread_join(threadReceive, NULL);
  // // pthread_join(threadSend, NULL); 

  // Using std::thread instead of pthread
  // NavigationDynamicCommunicationTest * testPtr = new NavigationDynamicCommunicationTest();
  std::thread threadReceive(&NavigationDynamicCommunicationTest::ReceiveFromSlicer, this);
  //threadReceive.detach();
  std::thread threadSend(&NavigationDynamicCommunicationTest::SendToSlicer, this);

  std::this_thread::sleep_for(std::chrono::seconds(60));
  return SUCCESS;
}