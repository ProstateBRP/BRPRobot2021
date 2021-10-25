/*=========================================================================
  Program:   OpenIGTLink -- Example for Tracker Server Program
  Language:  C++
  Copyright (c) Insight Software Consortium. All rights reserved.
  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.
=========================================================================*/

#include <iostream>
#include <math.h>
#include <cstdlib>
#include "Client.hxx"
#include <cstring>
#include <string>

#include "script.hxx"

Client::Client(char* hostname, int port)
{
  _clientSocketConnected = 0;
  socket = igtl::ClientSocket::New();
  _hostname = hostname;
  _port = port;
  status = "Not_Connected";
  cached_start_up_status = "Not_Connected";
  start_up_status = "";
}

// const char *testString[N_STRINGS] = {
//     "START_UP",
//     // "GET_STATUS",
//     // "GET_TRANSFORM",
//     // "PLANNING",
//     // "CALIBRATION",
//     // "TARGETING",
//     // "STOP",
//     // "EMERGENCY",
// };

void *Client::ThreadIGT(void *igt)
{

  // Get an IGT Object
  Client *igtModule = (Client *)igt;

  // Connect to server on the provided port
  igtl::ClientSocket::Pointer socket;
  socket = igtl::ClientSocket::New();
  int r = socket->ConnectToServer(igtModule->_hostname, igtModule->_port);
  
  if (r != 0)
  {
    std::cerr << "Cannot connect to the server." << std::endl;
    exit(0);
  }

  // While we are listening on this port
  while (1)
  {

    // Check if we can connect on the client socket
    // igtModule->socket = serverSocket->WaitForConnection(1000);

    // Connection Specific Variables State -- Not Connected
    igtModule->status = "Listening";
    igtModule->_clientSocketConnected = 0;

    // If we were able to connect to the client socket
    if (igtModule->socket.IsNotNull())
    {
      // Connection Specific Variables State -- Connected
      igtModule->status = "Connected";
      igtModule->_clientSocketConnected = -1;

      // Create a message buffer to receive header
      igtl::MessageHeader::Pointer headerMsg;
      headerMsg = igtl::MessageHeader::New();

      // Allocate a time stamp
      igtl::TimeStamp::Pointer ts;
      ts = igtl::TimeStamp::New();

      // While the socket is not null and we're connected to the the client socket
      while (igtModule->socket.IsNotNull() && igtModule->_clientSocketConnected != 0)
      {

        // Initialize receive buffer
        // Receive generic header from the socket
        headerMsg->InitPack();

        // To preserve asynchonicity set a time out for how long to wait to receive data
        igtModule->socket->SetReceiveTimeout(1000); // In milliseconds
        bool timeOut = false;
        // -- The _clientSocketConnected variable becomes zero when the Receive method is no longer connected to the client
        igtModule->_clientSocketConnected = igtModule->socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize(), timeOut);

        // Check that the received data is valid, else just listen again
        if (igtModule->_clientSocketConnected > 0)
        {

          // De-serialize the header
          headerMsg->Unpack();

          // Get time stamp
          igtlUint32 sec;
          igtlUint32 nanosec;
          headerMsg->GetTimeStamp(ts);
          ts->GetTimeStamp(&sec, &nanosec);

          //==========================================================================================
          //==========================================================================================
          // OPENIGTLINK MRI ROBOT RX PROTOCOLS

          //  REQUEST: NAME -- CURRENT_POSE & TYPE -- TRANSFORM
          if ((strcmp(headerMsg->GetDeviceName(), "START_UP") == 0) && (strcmp(headerMsg
                                                                                   ->GetDeviceType(),
                                                                               "STRING") == 0))
          {
            igtModule->ReceiveString(igtModule->socket, headerMsg);
            igtModule->start_up_status = headerMsg->GetDeviceName();
          }
          
          // REQUEST: TYPE -- UNKNOWN
          else
          {
            igtModule->socket->Skip(headerMsg->GetBodySizeToRead(), 0);
          }
        }
      }
    }
  }
}

// Send messages to WPI when the cached start_up_status is different from the current start_up_status
void Client::Sync()
{
  if (socket.IsNotNull() && _clientSocketConnected != 0)
  {

    if (!strcmp(start_up_status.c_str(), cached_start_up_status.c_str()))
    { 
      igtl::StringMessage::Pointer startUpMsg = igtl::StringMessage::New();

      startUpMsg->SetDeviceName("START_UP");
      startUpMsg->SetString("RECEIVED");
      startUpMsg->Pack();
      socket->Send(startUpMsg->GetPackPointer(), startUpMsg->GetPackSize());
    }
  }
}

std::string Client::ReceiveString(igtl::Socket *socket, igtl::MessageHeader *header)
{

  // Create a message buffer to receive transform data
  igtl::StringMessage::Pointer strMsg;
  strMsg = igtl::StringMessage::New();
  strMsg->SetMessageHeader(header);
  strMsg->AllocatePack();
  bool arg = false;
  // Receive transform data from the socket
  socket->Receive(strMsg->GetPackBodyPointer(),
                  strMsg->GetPackBodySize(), arg);

  // Deserialize the string data
  // If you want to skip CRC check, call Unpack() without argument.
  int c = strMsg->Unpack();
  std::string stringMessage = "";

  if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
  {
    stringMessage = strMsg->GetString();
  }

  SendStringToSlicer(slicerHostname, slicerPort, deviceName, message);
  std::cout << "Called SendStringToSlicer function in Lisa's script with argMessage = " << strMsg->GetString() << std::endl;

  return stringMessage;
}