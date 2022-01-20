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
#include <algorithm>
#include <cctype>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"

#include "NavigationBridge.h"
#include "NavigationSlicerScript.hxx"
#include "chrono"
#include "thread"


NavigationBridge::NavigationBridge()
{
}

NavigationBridge::~NavigationBridge()
{
}

// Threaded function to receive messages from Slicer via updated global variables and pass them along to WPI
void *NavigationBridge::ReceiveFromSlicer()
{
  std::cerr << "---> Starting thread II." << std::endl;

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
    if (currentStringMessage.compare(Global::globalString) != 0)
    {
      // Check to make sure the new message is all alphanumeric
      currentStringMessage = Global::globalString;
      if (isalpha(currentStringMessage[0]))
      {
        std::cout << "Sent stringMessage from Slicer to WPI: " << Global::globalString << std::endl;
        SendStringMessage(Global::globalDeviceName.c_str(), currentStringMessage.c_str());
      }

      // std::cout << "Sent stringMessage from Slicer to WPI: " << Global::globalString << std::endl;
      // currentStringMessage = Global::globalString;
      // SendStringMessage(Global::globalDeviceName.c_str(), currentStringMessage.c_str());
    }

    // New statusMessage from Slicer
    if (currentStatusArgErrorName.compare(Global::globalArgErrorName) != 0 || 
      currentStatusArgStatusStringMessage.compare(Global::globalArgStatusStringMessage) != 0 ||
      currentStatusArgCode != Global::globalArgCode ||
      currentStatusArgSubCode != Global::globalArgSubcode)
    {
      currentStatusArgCode = Global::globalArgCode;
      currentStatusArgSubCode = Global::globalArgSubcode;
      currentStatusArgErrorName = Global::globalArgErrorName;
      currentStatusArgStatusStringMessage = Global::globalArgStatusStringMessage;
      // Check to make sure the new message is all alphanumeric
      if (isalpha(currentStatusArgStatusStringMessage[0]))
      {
        std::cout << "Sent statusMessage from Slicer to WPI: " << Global::globalArgStatusStringMessage << std::endl;
        SendStatusMessage(Global::globalDeviceName.c_str(), currentStatusArgCode, currentStatusArgSubCode, (currentStatusArgErrorName).c_str(), (currentStatusArgStatusStringMessage).c_str());

        std::cerr << "========== STATUS ==========" << std::endl;
        std::cerr << " Code      : " << Global::globalArgCode << std::endl;
        std::cerr << " SubCode   : " << Global::globalArgSubcode << std::endl;
        std::cerr << " Error Name: " << Global::globalArgErrorName << std::endl;
        std::cerr << " Status    : " << Global::globalArgStatusStringMessage << std::endl;
        std::cerr << "============================" << std::endl;
      }

      // std::cout << "Sent statusMessage from Slicer to WPI: " << Global::globalArgStatusStringMessage << std::endl;
      // currentStatusArgCode = Global::globalArgCode;
      // currentStatusArgSubCode = Global::globalArgSubcode;
      // currentStatusArgErrorName = Global::globalArgErrorName;
      // currentStatusArgStatusStringMessage = Global::globalArgStatusStringMessage;
      // SendStatusMessage(Global::globalDeviceName.c_str(), currentStatusArgCode, currentStatusArgSubCode, (currentStatusArgErrorName).c_str(), (currentStatusArgStatusStringMessage).c_str());

      // std::cerr << "========== STATUS ==========" << std::endl;
      // std::cerr << " Code      : " << Global::globalArgCode << std::endl;
      // std::cerr << " SubCode   : " << Global::globalArgSubcode << std::endl;
      // std::cerr << " Error Name: " << Global::globalArgErrorName << std::endl;
      // std::cerr << " Status    : " << Global::globalArgStatusStringMessage << std::endl;
      // std::cerr << "============================" << std::endl;
    }

    // New transformMessage from Slicer
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 4; j++)
      {
        if (currentMatrix[i][j] != Global::globalMatrix[i][j])
        {
          std::cout << "Sent transformMessage from Slicer to WPI: " << std::endl;
          SendTransformMessage(Global::globalDeviceName.c_str(), currentMatrix);
          memcpy(currentMatrix, Global::globalMatrix, sizeof(Global::globalMatrix));
          igtl::PrintMatrix(currentMatrix);
        }
      }
    }
  }
  return NULL;
}

// Threaded function to receive messages from WPI and send to Slicer via NavigationSlicerScript.cxx
void *NavigationBridge::SendToSlicer()
{
  std::cerr << "---> Starting thread III." << std::endl;
  while(1)
  {
	std::this_thread::sleep_for(std::chrono::seconds(1));
	igtl::MessageHeader::Pointer headerMsg;
	headerMsg = igtl::MessageHeader::New();
    ReceiveMessageHeader(headerMsg, this->TimeoutFalse);
    // std::cout << "Incoming message from WPI with deviceType: " << headerMsg->GetDeviceType() << " and deviceName: " << headerMsg->GetDeviceName() << std::endl;
    
    // Incoming message is a stringMessage --> receive stringMessage from WPI and send to Slicer
    if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
    {
      ReceiveString(headerMsg);
    }

    // Incoming message is a statusMessage --> receive statusMessage from WPI and send to Slicer
    if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
    {
      ReceiveStatus(headerMsg);
    }

    // Incoming message is a transformMessage --> receive transformMessage from WPI and send to Slicer
    if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
    {
      ReceiveTransform(headerMsg);
    }
  }
  return NULL;
}


NavigationBridge::ErrorPointType NavigationBridge::Test()
{
  // Create a thread to receive from Slicer and send to WPI
  std::thread threadReceive(&NavigationBridge::ReceiveFromSlicer, this);
  threadReceive.detach();
  std::thread threadSend(&NavigationBridge::SendToSlicer, this);
  threadSend.detach();

  std::this_thread::sleep_for(std::chrono::seconds(36000));
  //return SUCCESS;
  return 0;
}