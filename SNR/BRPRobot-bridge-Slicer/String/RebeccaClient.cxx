/*=========================================================================

  Program:   OpenIGTLink -- Example for String Message Client Program
  Module:    $RCSfile: $
  Language:  C++
  Date:      $Date: $
  Version:   $Revision: $

  Copyright (c) Insight Software Consortium. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"

#include "LisaScript.h"


int main(int argc, char* argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

  if (argc != 4) // check number of arguments
  {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>"    << std::endl;
    std::cerr << "    <hostname> : IP or host name"                    << std::endl;
    std::cerr << "    <port>     : Port # (18944 in Slicer default)"   << std::endl;
    std::cerr << "    <fps>      : Frequency (fps) to send string" << std::endl;
    exit(0);
  }

  char*  hostname = argv[1];
  int    port     = atoi(argv[2]);
  double fps      = atof(argv[3]);
  int    interval = (int) (1000.0 / fps);

  //------------------------------------------------------------
  // Establish Connection

  igtl::ClientSocket::Pointer socket;
  socket = igtl::ClientSocket::New();
  int r = socket->ConnectToServer(hostname, port);

  if (r != 0)
  {
    std::cerr << "Cannot connect to the server." << std::endl;
    exit(0);
  }

  while (1)
  {
    //------------------------------------------------------------
    // Waiting for Connection
    // socket = serverSocket->WaitForConnection(1000);
    igtl::MessageHeader::Pointer hdrMsg = igtl::MessageHeader::New();

    while (socket.IsNotNull() && socket->GetConnected())
    {      
      hdrMsg->InitPack();
      bool timeout(false);
      igtlUint64 r = socket->Receive(hdrMsg->GetPackPointer(), hdrMsg->GetPackSize(), timeout);

      // check message
      if (r == 0) 
        {
        socket->CloseSocket();
        continue;
        }
      if (r != hdrMsg->GetPackSize())
        continue;

      // get data
      hdrMsg->Unpack();
      igtl::StringMessage::Pointer strMsg(igtl::StringMessage::New());
      strMsg->SetMessageHeader(hdrMsg);
      strMsg->AllocatePack();
      timeout = false;
      socket->Receive(strMsg->GetPackBodyPointer(), strMsg->GetPackBodySize(), timeout);
      int c = strMsg->Unpack();

      // echo message back
      std::cout << "Echoing message from WPI: " << strMsg->GetString() << std::endl;
      strMsg->SetDeviceName("StringEchoClient");
      strMsg->Pack();
      socket->Send(strMsg->GetPackPointer(), strMsg->GetPackSize());

      // Enter different phases of the protocol based on the message from WPI
      if ( strMsg->GetString() == "START_UP" )
      {
        // Call Startup function in Lisa's script
        startup();
        std::cout << "Called startup function in Lisa's script." << std::endl;
        //std::string status = getStatus();
        int status = getStatus();
        //std::cout << "The current status is: " << status << std::endl;

      }

      else if ( strMsg->GetString() == "GET_TRANSFORM" )
      {
        // Call GetTransform function in Lisa's script
        //std::string transform = getTransform();
        std::cout << "Called getTransform function in Lisa's script." << std::endl;

      }

      else if ( strMsg->GetString() == "GET_STATUS" )
      {
        // Call GetStatus function in Lisa's script
        //std::string status = getStatus();
        std::cout << "Called getStatus function in Lisa's script." << std::endl;
        //std::cout << "The current status is: " << status << std::endl;

      }

    }
  }

  //------------------------------------------------------------
  // Close connection

  socket->CloseSocket();
}
