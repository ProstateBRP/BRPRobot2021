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

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include "igtlServerSocket.h"

#define N_STRINGS 1

const char * testString[N_STRINGS] = {
  "START_UP",
  // "GET_STATUS",
  // "GET_TRANSFORM",
  // "PLANNING",
  // "CALIBRATION",
  // "TARGETING",
  // "STOP",
  // "EMERGENCY",
};

void GetRandomTestMatrix(igtl::Matrix4x4& matrix);

int main(int argc, char* argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

  if (argc != 3) // check number of arguments
  {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <port> <fps>"    << std::endl;
    std::cerr << "    <port>     : Port # (18944 in Slicer default)"   << std::endl;
    std::cerr << "    <fps>      : Frequency (fps) to send string" << std::endl;
    exit(0);
  }

  int    port     = atoi(argv[1]);
  double fps      = atof(argv[2]);
  int    interval = (int) (1000.0 / fps);

  //------------------------------------------------------------
  // Allocate String Message Class

  igtl::StringMessage::Pointer stringMsg;
  stringMsg = igtl::StringMessage::New();
  stringMsg->SetDeviceName("StringMessage");

  //------------------------------------------------------------
  // Allocate Status Message Class

  igtl::StatusMessage::Pointer statusMsg;
  statusMsg = igtl::StatusMessage::New();
  statusMsg->SetDeviceName("Device");

  //------------------------------------------------------------
  // Allocate Transform Message Class

  igtl::TransformMessage::Pointer transMsg;
  transMsg = igtl::TransformMessage::New();
  transMsg->SetDeviceName("Tracker");

  //------------------------------------------------------------
  // Create Server Socket

  igtl::ServerSocket::Pointer serverSocket;
  serverSocket = igtl::ServerSocket::New();
  int r = serverSocket->CreateServer(port);

  if (r < 0)
  {
    std::cerr << "Cannot create a server socket." << std::endl;
    exit(0);
  }

  igtl::Socket::Pointer socket;
  
  while (1)
  {
    //------------------------------------------------------------
    // Waiting for Connection
    socket = serverSocket->WaitForConnection(1000);
    
    if (socket.IsNotNull()) // if client connected
    {
      //------------------------------------------------------------
      // Send testStrings in stringMessage format
      for (int i = 0; i < N_STRINGS; i ++)
      {
        std::cout << "Sending string: " << testString[i%N_STRINGS] << std::endl;
        stringMsg->SetDeviceName("StringMessage");
        stringMsg->SetString(testString[i%N_STRINGS]);
        stringMsg->Pack();
        socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());
        igtl::Sleep(interval); // wait
      }

      // Send a statusMessage
      statusMsg->SetCode(igtl::StatusMessage::STATUS_OK);
      statusMsg->SetSubCode(128);
      statusMsg->SetErrorName("OK!");
      statusMsg->SetStatusString("This is a test to send a status message.");
      statusMsg->Pack();
      socket->Send(statusMsg->GetPackPointer(), statusMsg->GetPackSize());
      igtl::Sleep(interval); // wait

      // Send a transformMessage
      igtl::Matrix4x4 matrix;
      GetRandomTestMatrix(matrix);
      transMsg->SetMatrix(matrix);
      transMsg->Pack();
      socket->Send(transMsg->GetPackPointer(), transMsg->GetPackSize());
      igtl::Sleep(interval); // wait

    }
  }
    
  //------------------------------------------------------------
  // Close connection (The example code never reachs to this section ...)
  
  socket->CloseSocket();

}


//------------------------------------------------------------
// Function to generate random matrix.

void GetRandomTestMatrix(igtl::Matrix4x4& matrix)
{
  float position[3];
  float orientation[4];

  // random position
  static float phi = 0.0;
  position[0] = 50.0 * cos(phi);
  position[1] = 50.0 * sin(phi);
  position[2] = 50.0 * cos(phi);
  phi = phi + 0.2;

  // random orientation
  static float theta = 0.0;
  orientation[0]=0.0;
  orientation[1]=0.6666666666*cos(theta);
  orientation[2]=0.577350269189626;
  orientation[3]=0.6666666666*sin(theta);
  theta = theta + 0.1;

  //igtl::Matrix4x4 matrix;
  igtl::QuaternionToMatrix(orientation, matrix);

  matrix[0][3] = position[0];
  matrix[1][3] = position[1];
  matrix[2][3] = position[2];
  
  igtl::PrintMatrix(matrix);
}

