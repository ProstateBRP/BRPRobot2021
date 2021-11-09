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
#include "Server.hxx"
#include <cstring>
#include <string>
Server::Server(int port)
{
  _clientSocketConnected = 0;
  socket = igtl::ClientSocket::New();
  _port = port;
  status = "Not_Connected";
  cached_start_up_status = "Not_Connected";
  start_up_status = "";
}

void *Server::ThreadIGT(void *igt)
{

  // Get an IGT Object
  Server *igtModule = (Server *)igt;

  // Create New Sockets on the provided port
  igtl::ServerSocket::Pointer serverSocket;
  serverSocket = igtl::ServerSocket::New();
  int r = serverSocket->CreateServer(igtModule->_port);

  // Check if we can create a server socket
  if (r < 0)
  {
    // If we cannot error back
    std::cerr << "Cannot create a server socket." << std::endl;
    exit(1);
  }

  // While we are listening on this port
  while (1)
  {

    // Check if we can connect on the client socket
    igtModule->socket = serverSocket->WaitForConnection(1000);

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

          // // REQUEST: NAME -- REGISTRATION & TYPE -- TRANSFORM
          // else if ((strcmp(headerMsg->GetDeviceName(), "REGISTRATION") == 0) && (strcmp(headerMsg
          //                                                                                   ->GetDeviceType(),
          //                                                                               "TRANSFORM") == 0))
          // {
          //   igtModule->_robot->_registration = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
          //   log.Log("OpenIGTLink Registration Received and Set in Code", LOG_LEVEL_INFO, true);
          // }

          // // REQUEST: NAME -- TIP POSE & TYPE -- TRANSFORM wrt to imager plane
          // else if ((strcmp(headerMsg->GetDeviceName(), "TIP_POSE") == 0) && (strcmp(headerMsg
          //                                                                               ->GetDeviceType(),
          //                                                                           "TRANSFORM") == 0))
          // {
          //   igtModule->_robot->_imagerTip = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
          //   igtModule->_robot->RunInverseKinematics(0);
          //   log.Log("OpenIGTLink Tip Pose Received and Set in Code", LOG_LEVEL_INFO, true);
          // }

          // // REQUEST: TYPE -- STRING
          // else if ((strcmp(headerMsg->GetDeviceName(), "TARGET_STATUS") == 0) && (strcmp(headerMsg
          //                                                                                    ->GetDeviceType(),
          //                                                                                "STRING") == 0))
          // {
          //   igtModule->_robot->_imagerStatus = igtModule->ReceiveString(igtModule->socket, headerMsg);
          //   log.Log("Target Status: " + igtModule->_robot->_imagerStatus, LOG_LEVEL_INFO, true);
          // }

          // // REQUEST: TYPE -- STATUS
          // else if (strcmp(headerMsg->GetDeviceName(), "GET_STATUS") == 0)
          // {
          //   // Send status messages
          //   igtl::StatusMessage::Pointer statusMsg = igtl::StatusMessage::New();
          //   statusMsg->SetDeviceName("STATUS");
          //   statusMsg->SetCode(1);
          //   statusMsg->Pack();
          //   igtModule->socket->Send(statusMsg->GetPackPointer(), statusMsg->GetPackSize());

          //   // If we are keeping track of the client keep alive messages
          //   if (igtModule->_keepAlive)
          //   {
          //     igtModule->_keepAliveTimer.tic();
          //   }
          // }

          // // REQUEST: NAME -- ABLATION_ANGLE & REQUEST: TYPE -- STRING
          // else if ((strcmp(headerMsg->GetDeviceName(), "ABLATION_ANGLE") == 0) && (strcmp(headerMsg
          //                                                                                     ->GetDeviceType(),
          //                                                                                 "STRING") == 0))
          // {
          //   // Specific to NeuroRobot
          //   // Receive angle in radians from MATLAB Lesion Map Simulation Code
          //   string angle = igtModule->ReceiveString(igtModule->socket, headerMsg);

          //   Motor *_motor = igtModule->_robot->GetMotor(1);               // Only for NeuroRobot
          //   _motor->_setpoint = int(stod(angle) * _motor->_ticksPerUnit); // convert to ticks
          //                                                                 // log.Log("Ablation Angle: " + angle, LOG_LEVEL_INFO, true);
          // }

          // // REQUEST: NAME -- ENTRY_POINT & REQUEST: TYPE -- TRANSFORM
          // else if ((strcmp(headerMsg->GetDeviceName(), "ENTRY_POINT") == 0) && (strcmp(headerMsg
          //                                                                                  ->GetDeviceType(),
          //                                                                              "TRANSFORM") == 0))
          // {
          //   //
          //   Eigen::Matrix4d entryPointScannerCoordinates = igtModule->ReceiveTransform(igtModule->socket, headerMsg);

          //   igtModule->_robot->_entryPoint(0) = (double)entryPointScannerCoordinates(0, 3);
          //   igtModule->_robot->_entryPoint(1) = (double)entryPointScannerCoordinates(1, 3);
          //   igtModule->_robot->_entryPoint(2) = (double)entryPointScannerCoordinates(2, 3);

          //   // Recalculate InverseKinematics and Setpoints
          //   igtModule->_robot->RunInverseKinematics(1);
          //   log.Log("OpenIGTLink Entry Point Received and Set in Code", LOG_LEVEL_INFO, true);
          // }

          // // REQUEST: NAME -- TARGET_POINT & REQUEST: TYPE -- TRANSFORM
          // else if ((strcmp(headerMsg->GetDeviceName(), "TARGET_POINT") == 0) && (strcmp(headerMsg
          //                                                                                   ->GetDeviceType(),
          //                                                                               "TRANSFORM") == 0))
          // {
          //   //
          //   // Eigen::Matrix4d targetPoseRobot = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
          //   // Eigen::Matrix4d targetPointScannerCoordinates = targetPoseRobot;
          //   Eigen::Matrix4d targetPointScannerCoordinates = igtModule->ReceiveTransform(igtModule->socket,
          //                                                                               headerMsg);

          //   igtModule->_robot->_targetPoint(0) = (double)targetPointScannerCoordinates(0, 3);
          //   igtModule->_robot->_targetPoint(1) = (double)targetPointScannerCoordinates(1, 3);
          //   igtModule->_robot->_targetPoint(2) = (double)targetPointScannerCoordinates(2, 3);
          //   // Giving full target pose to the robot as well. Is used for the NeuroRobot
          //   igtModule->_robot->_targetPointFullPoseScanner = targetPointScannerCoordinates;

          //   // Recalculate InverseKinematics and Setpoints
          //   igtModule->_robot->RunInverseKinematics(1);
          //   log.Log("OpenIGTLink Target Point Received and Set in Code", LOG_LEVEL_INFO, true);
          // }

          //==========================================================================================
          //==========================================================================================

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
void Server::Sync()
{
  if (socket.IsNotNull() && _clientSocketConnected != 0)
  {

    if (!strcmp(start_up_status.c_str(), cached_start_up_status.c_str()))
    { // Create Transformation Matrix to transmit
      igtl::StringMessage::Pointer startUpMsg = igtl::StringMessage::New();

      startUpMsg->SetDeviceName("START_UP");
      startUpMsg->SetString("RECEIVED");
      startUpMsg->Pack();
      socket->Send(startUpMsg->GetPackPointer(), startUpMsg->GetPackSize());
    }
  }
}

std::string Server::ReceiveString(igtl::Socket *socket, igtl::MessageHeader *header)
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
  return stringMessage;
}
