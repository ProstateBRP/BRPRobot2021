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
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include "igtlClientSocket.h"
#include "pthread.h"

#include "script.hxx"

// Global variables
char *hostname;
int port;
char *slicerHostname;
int slicerPort;
double fps;
int interval;
char *deviceName;

// Struct for thread arguments (socket)
struct ThreadArg {
  char *hostname; 
  int port;
};


void* receiveFromWPI( void *arg )
{

  struct ThreadArg *thArg = (struct ThreadArg *)arg;
  char *hostname = thArg->hostname;
  int port = thArg->port;
  free(arg);
  
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

      // Message is a StringMessage
      if (strcmp(hdrMsg->GetDeviceType(), "STRING") == 0)
      {
        igtl::StringMessage::Pointer strMsg(igtl::StringMessage::New());
        strMsg->SetMessageHeader(hdrMsg);
        strMsg->AllocatePack();
        timeout = false;
        socket->Receive(strMsg->GetPackBodyPointer(), strMsg->GetPackBodySize(), timeout);
        int c = strMsg->Unpack();

        // Echo message back
        std::cout << "Echoing message from WPI: " << strMsg->GetString() << std::endl;
        strMsg->SetDeviceName("StringEchoClient");
        strMsg->Pack();
        socket->Send(strMsg->GetPackPointer(), strMsg->GetPackSize());

        char *message = (char *)(strMsg->GetString());

        // Enter different phases of the protocol based on the content of the string message from WPI
        // if ( strcmp(strMsg->GetString(), "START_UP") == 0 )
        //{

        // Call SendStringToSlicer function in Lisa's script
        SendStringToSlicer(slicerHostname, slicerPort, deviceName, message);
        std::cout << "Called SendStringToSlicer function in Lisa's script with argMessage = " << strMsg->GetString() << std::endl;

        int status = getStatus();
        std::cout << "The current status is: " << status << std::endl;
        std::cout << "---------------------------------------------\n"
                  << std::endl;

        //}
      }

      // Message is a StatusMessage
      else if (strcmp(hdrMsg->GetDeviceType(), "STATUS") == 0)
      {
        igtl::StatusMessage::Pointer statusMsg;
        statusMsg = igtl::StatusMessage::New();
        statusMsg->SetMessageHeader(hdrMsg);
        statusMsg->AllocatePack();
        timeout = false;
        socket->Receive(statusMsg->GetPackBodyPointer(), statusMsg->GetPackBodySize(), timeout);

        // Send the contents of the statusMessage to LisaScript
        unsigned short argCode = statusMsg->GetCode();
        unsigned long long argSubcode = statusMsg->GetSubCode();
        char *argErrorName = (char *)(statusMsg->GetErrorName());
        char *argStatusStringMessage = (char *)(statusMsg->GetStatusString());

        SendStateToSlicer(slicerHostname, slicerPort, deviceName, argCode, argSubcode, argErrorName, argStatusStringMessage);
        std::cout << "Called SendStateToSlicer function in Lisa's script." << std::endl;

        int status = getStatus();
        std::cout << "The current status is: " << status << std::endl;
        std::cout << "---------------------------------------------\n"
                  << std::endl;
      }

      // Message is a TransformMessage
      else if (strcmp(hdrMsg->GetDeviceType(), "TRANSFORM") == 0)
      {
        igtl::TransformMessage::Pointer transMsg;
        transMsg = igtl::TransformMessage::New();
        transMsg->SetMessageHeader(hdrMsg);
        transMsg->AllocatePack();
        timeout = false;
        socket->Receive(transMsg->GetPackBodyPointer(), transMsg->GetPackBodySize(), timeout);

        int c = transMsg->Unpack(1);
        if (c & igtl::MessageHeader::UNPACK_BODY)
        {
          // if CRC check is OK. Read transform data.
          igtl::Matrix4x4 matrix;
          transMsg->GetMatrix(matrix);
          igtl::PrintMatrix(matrix);

          // Send the contents of the transformMessage to LisaScript
          SendTransformToSlicer(slicerHostname, slicerPort, deviceName, matrix);
          std::cout << "Called SendTransformToSlicer function in Lisa's script." << std::endl;

          int status = getStatus();
          std::cout << "The current status is: " << status << std::endl;
          std::cout << "---------------------------------------------\n"
                    << std::endl;
        }
      }
    }
  }

  pthread_exit(NULL);
  return NULL;
}

// void* sendToWPI( void * arg )
// {

//   while(1)
//   {

//     // Allocate Transform Message Class
//     igtl::StringMessage::Pointer stringMsg;
//     stringMsg = igtl::StringMessage::New();

//     // Startup protocol - Send startup command to WPI server
//     stringMsg->SetDeviceName("StringMessage");
//     std::cout << "Sending string: START_UP" << std::endl;
//     stringMsg->SetString("START_UP");
//     stringMsg->Pack();
//     socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());


//   }
//     pthread_exit(NULL);
// }

int main(int argc, char *argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

  if (argc != 6) // check number of arguments
  {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>" << std::endl;
    std::cerr << "    <hostname> : IP or host name for WPI server connection" << std::endl;
    std::cerr << "    <port>     : Port # for WPI server connection" << std::endl;
    std::cerr << "    <slicerHostname> : IP or host name for Slicer server connection" << std::endl;
    std::cerr << "    <slicerPort>     : Port # for Slicer server connection" << std::endl;
    std::cerr << "    <fps>      : Frequency (fps) to send string" << std::endl;
    exit(0);
  }

  // char *hostname = argv[1];
  // int port = atoi(argv[2]);
  // char *slicerHostname = argv[3];
  // int slicerPort = atoi(argv[4]);
  // double fps = atof(argv[5]);
  // int interval = (int)(1000.0 / fps);
  // char *deviceName = (char *)"deviceName";

  hostname = argv[1];
  port = atoi(argv[2]);
  slicerHostname = argv[3];
  slicerPort = atoi(argv[4]);
  fps = atof(argv[5]);
  interval = (int)(1000.0 / fps);
  deviceName = (char *)"deviceName";


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

  // Struct for thread arguments (socket)
  struct ThreadArg *arg;
  arg->hostname = hostname;
  arg->port = port;


  pthread_t thread;
  pthread_create(&thread, NULL, receiveFromWPI, (void*)arg);
  // pthread_t thread2;
  // pthread_create(&thread2, NULL, sendToWPI, NULL);


  // While the receiveFromWPI thread is running, also enter a second loop in main to send messages to WPI
  while(1)
  {

    // Allocate Transform Message Class
    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();

    // Startup protocol - Send startup command to WPI server
    stringMsg->SetDeviceName("StringMessage");
    std::cout << "Sending string to WPI: START_UP" << std::endl;
    stringMsg->SetString("START_UP");
    stringMsg->Pack();
    socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());


  }


  //------------------------------------------------------------
  // Close connection

  socket->CloseSocket();
}
