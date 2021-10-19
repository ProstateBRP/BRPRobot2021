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
#include "igtlServerSocket.h"


#define N_STRINGS 5

const char * testString[N_STRINGS] = {
  "START_UP",
  "Network",
  "Communication",
  "Protocol",
  "Image Guided Therapy",
};

int main(int argc, char* argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

  if (argc != 5) // check number of arguments
    {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>"    << std::endl;
    std::cerr << "    <hostname> : IP or host name"                    << std::endl;
    std::cerr << "    <client port>     : Port # for connection as a client"   << std::endl;
    std::cerr << "    <server port>     : Port # for connection as a server"   << std::endl;
    std::cerr << "    <fps>      : Frequency (fps) to send string" << std::endl;
    exit(0);
    }

  char*  hostname   = argv[1];
  int    clientPort = atoi(argv[2]);
  int    serverPort = atoi(argv[3]);
  double fps        = atof(argv[4]);
  int    interval   = (int) (1000.0 / fps);

  //------------------------------------------------------------
  // Establish Connection as a CLIENT (to receive messages from the WPI robot/bridge server)

  igtl::ClientSocket::Pointer socket;
  socket = igtl::ClientSocket::New();
  int r = socket->ConnectToServer(hostname, clientPort);

  if (r != 0)
    {
    std::cerr << "Cannot connect to the server." << std::endl;
    exit(0);
    }

  //------------------------------------------------------------
  // Allocate Transform Message Class

  igtl::StringMessage::Pointer clientStringMsg;
  clientStringMsg = igtl::StringMessage::New();
  


  // Establish Connection as a SERVER (to send messages to Lisa's client)
  igtl::StringMessage::Pointer serverStringMsg;
  serverStringMsg = igtl::StringMessage::New();
  serverStringMsg->SetDeviceName("ServerStringMessage");

  igtl::ServerSocket::Pointer serverSocket;
  serverSocket = igtl::ServerSocket::New();
  int q = serverSocket->CreateServer(serverPort);

  if (q < 0)
    {
    std::cerr << "Cannot create a server socket." << std::endl;
    exit(0);
    }

  igtl::Socket::Pointer newSocket;


  //------------------------------------------------------------
  // loop
  int i = 0;
  while (1)
    {
      std::cout << "(Client mode) ";
      clientStringMsg->SetDeviceName("StringMessage");
      std::cout << "Receiving string from WPI server: " << testString[i] << std::endl;
      clientStringMsg->SetString(testString[i]);
      clientStringMsg->Pack();
      socket->Send(clientStringMsg->GetPackPointer(), clientStringMsg->GetPackSize());
      igtl::Sleep(interval); // wait

    // Waiting for Connection
    newSocket = serverSocket->WaitForConnection(1000);
    
    if (newSocket.IsNotNull()) // if client connected
      {
      //------------------------------------------------------------
      // loop
      for (i = 0; i < 10; i ++)
        {
          std::cout << "(Server mode) ";
          std::cout << "Sending string to Lisa: " << testString[i] << std::endl;
          serverStringMsg->SetDeviceName("StringMessage");
          serverStringMsg->SetString(testString[i]);
          serverStringMsg->Pack();
          newSocket->Send(serverStringMsg->GetPackPointer(), serverStringMsg->GetPackSize());
          igtl::Sleep(interval); // wait
        }
      }
    }

  //------------------------------------------------------------
  // Close connection

  socket->CloseSocket();
}
