/*=========================================================================

  Program:   BRP Prostate Robot 2021
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    https://github.com/ProstateBRP/BRPRobot2021/wiki
  for the detail of the protocol.

=========================================================================*/

#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include "igtlClientSocket.h"
#include "NavigationSlicerScript.hxx"
#include "thread"
#include "igtlMath.h"


// Set default values for the hostname and port (to be updated by a function call to setSocketVars)
char * Global::hostname = (char*)"localhost";
int Global::port = 18944;
bool Global::testRunning = true;
std::string Global::globalDeviceName = "DefaultGlobalDeviceName";
// Default values for stringMessages, statusMessages, and transformMessage
std::string Global::globalString = "DefaultGlobalString";
int Global::globalArgCode = 0;
int Global::globalArgSubcode = 0;
std::string Global::globalArgErrorName = "DefaultGlobalArgErrorName";
std::string Global::globalArgStatusStringMessage = "DefaultArgStatusStringMessage";
igtl::Matrix4x4 Global::globalMatrix = {{0,0,0,0},
                                        {0,0,0,0},
                                        {0,0,0,0},
                                        {0,0,0,0}};


void setSocketVars(char* snrHostname, int snrPort)
{
    Global::hostname = snrHostname;
    Global::port = snrPort;
}

void *startThread()
{
    std::cout << "\n---> Starting thread I." << std::endl;
    // Create thread for the receiving function
	std::thread thr(&receivingFunction);
	thr.detach();

    return NULL;
}

// Another function here that is continuously run by the thread
void *receivingFunction()
{
    //------------------------------------------------------------
    // Establish Connection

    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();

    // Continuously running while loop to listen for messages from Slicer
    while (1)
    {
        // Initialize receive buffer
        headerMsg->InitPack();

        // Receive generic header from the socket

        bool timeout(false);
        igtlUint64 r = socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize(), timeout);
        if (r == 0)
        {
        socket->CloseSocket();
        exit(0);
        }
        if (r != headerMsg->GetPackSize())
        {
        continue;
        }

        // Deserialize the header
        headerMsg->Unpack();

        if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
        {
            ReceiveString(socket, headerMsg);
        }
        else if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
        {
            ReceiveStatus(socket, headerMsg);
        }
        else if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
        {
            ReceiveTransform(socket, headerMsg);
        }
    } 
    return NULL;
}


void SendStringToSlicer(char* argDeviceName, char* argMessage)
{
    //------------------------------------------------------------
    // Establish Connection

  
    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Allocate Transform Message Class

    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();
    //------------------------------------------------------------

    // Send string message

    stringMsg->SetDeviceName(argDeviceName);
    stringMsg->SetString(argMessage);
    stringMsg->Pack();
    socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());
    std::cout << "Sent stringMessage to Slicer with argMessage: " << argMessage << std::endl;

}

void SendStatusToSlicer(char *argDeviceName, unsigned short argCode, unsigned long long argSubcode, char *argErrorName, char *argStatusStringMessage)
{
    //------------------------------------------------------------
    // Establish Connection

    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Allocate Status Message Class

    igtl::StatusMessage::Pointer statusMsg;
    statusMsg = igtl::StatusMessage::New();
    statusMsg->SetDeviceName(argDeviceName);
    //------------------------------------------------------------

    int i = 0;
    while (i == 0)
    {
        statusMsg->SetCode(argCode);
        statusMsg->SetSubCode(argSubcode);
        statusMsg->SetErrorName(argErrorName);
        statusMsg->SetStatusString(argStatusStringMessage);
        statusMsg->Pack();
        socket->Send(statusMsg->GetPackPointer(), statusMsg->GetPackSize());
        std::cout << "Sent statusMessage to Slicer: " << argStatusStringMessage << std::endl;

        std::cerr << "========== STATUS ==========" << std::endl;
        std::cerr << " Code      : " << argCode << std::endl;
        std::cerr << " SubCode   : " << argSubcode << std::endl;
        std::cerr << " Error Name: " << argErrorName << std::endl;
        std::cerr << " Status    : " << argStatusStringMessage << std::endl;
        std::cerr << "============================" << std::endl;
        i = 1;
    }
}

void SendTransformToSlicer(char *argDeviceName, igtl::Matrix4x4 &matrix, char * wpiDeviceName)
{
    // Send TransformInfo to Slicer
    char *deviceNameTransformInfo = (char *)("TransformInfo");
    SendStringToSlicer(deviceNameTransformInfo, wpiDeviceName);
    //------------------------------------------------------------
    // Establish Connection

    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Allocate Transform Message Class

    igtl::TransformMessage::Pointer transMsg;
    transMsg = igtl::TransformMessage::New();
    transMsg->SetDeviceName(argDeviceName);
    
    std::cout << "Sent transformMessage to Slicer." << std::endl;

    igtl::TimeStamp::Pointer ts;
    ts = igtl::TimeStamp::New();
    ts->GetTime();

    int i = 0;
    while (i == 0)
    {
        transMsg->SetMatrix(matrix);
        transMsg->SetTimeStamp(ts);
        transMsg->Pack();

        int r = socket->Send(transMsg->GetPackPointer(), transMsg->GetPackSize());
        if (!r)
        {
            std::cerr << "Error Sending TRANSFORM " << std::endl;
            exit(0);
        }
        i = 1;
    }
}



void GetStringFromSlicer(const char* hostname, int port)
{
    //------------------------------------------------------------
    // Establish Connection

    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();

    //------------------------------------------------------------
    // Wait for String message from Slicer until it sends one string message

    std::cout << "inside GetStringFromSlicer debut " <<std::endl;
    bool StringReceived = 0;
    // loop
    while (StringReceived == 0)
    {
        std::cout << "Inside string receiver "  << std::endl; 
        // Initialize receive buffer
        headerMsg->InitPack();

        // Receive generic header from the socket

        bool timeout(false);
        igtlUint64 r = socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize(), timeout);
        if (r == 0)
        {
            socket->CloseSocket();
            exit(0);
        }
        if (r != headerMsg->GetPackSize())
        {
            continue;
        }

        // Deserialize the header
        headerMsg->Unpack();
        std::cout << "headerMsg is "  << headerMsg->GetDeviceType() <<std::endl; 

        ReceiveString(socket, headerMsg);
        StringReceived = 1;
        std::cout << "StringMessage received in NavigationSlicerScript.cxx from Slicer : " << Global::globalString << std::endl; 
        std::cout << "Current deviceName : " << Global::globalDeviceName << std::endl;
    }     
 }

void GetStatusFromSlicer(const char* hostname, int port)
{

    //------------------------------------------------------------
    // Establish Connection

    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();

    //------------------------------------------------------------
    // Wait for Status message from Slicer until it sends one status message

    bool StatusReceived = 0;
    // loop
    while (StatusReceived == 0)
    {
      // Initialize receive buffer
      headerMsg->InitPack();

      // Receive generic header from the socket

      bool timeout(false);
      igtlUint64 r = socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize(), timeout);
      if (r == 0)
      {
        socket->CloseSocket();
        exit(0);
      }
      if (r != headerMsg->GetPackSize())
      {
        continue;
      }

      // Deserialize the header
      headerMsg->Unpack();


      ReceiveStatus(socket, headerMsg);
      std::cout << "inside GetStatusFromSlicer " << headerMsg <<std::endl;
      StatusReceived = 1;
    }     
 }

void GetTransformFromSlicer(const char* hostname, int port)
{

    //------------------------------------------------------------
    // Establish Connection

    igtl::ClientSocket::Pointer socket;
    socket = igtl::ClientSocket::New();
    int r = socket->ConnectToServer(Global::hostname, Global::port);

    if (r != 0)
    {
        std::cerr << "Cannot connect to the server." << std::endl;
        exit(0);
    }

    //------------------------------------------------------------
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();

    //------------------------------------------------------------
    // Wait for TRANSFORM message from Slicer until it sends one transform message

    bool TransformReceived = 0;
    // loop
    while (TransformReceived == 0)
    {
      // Initialize receive buffer
      headerMsg->InitPack();

      // Receive generic header from the socket

      bool timeout(false);
      igtlUint64 r = socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize(), timeout);
      if (r == 0)
      {
        socket->CloseSocket();
        exit(0);
      }
      if (r != headerMsg->GetPackSize())
      {
        continue;
      }

      // Deserialize the header
      headerMsg->Unpack();

      ReceiveTransform(socket, headerMsg);
      TransformReceived = 1;
    }     
 }

int ReceiveString(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{
    // Create a message buffer to receive transform data
    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();
    stringMsg->SetMessageHeader(header);
    stringMsg->AllocatePack();

    // Receive transform data from the socket
    bool timeout(false);
    socket->Receive(stringMsg->GetPackBodyPointer(), stringMsg->GetPackBodySize(), timeout);

    // Deserialize the transform data
    // If you want to skip CRC check, call Unpack() without argument.

    int c = stringMsg->Unpack(1);

    std::cerr << "\n---> Received stringMessage from Slicer: " << stringMsg->GetString() << std::endl;
    Global::globalString = stringMsg->GetString();
    Global::globalDeviceName = header->GetDeviceName();

    return 1;
}


int ReceiveStatus(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{

    // Create a message buffer to receive transform data
    igtl::StatusMessage::Pointer statusMsg;
    statusMsg = igtl::StatusMessage::New();
    statusMsg->SetMessageHeader(header);
    statusMsg->AllocatePack();

    // Receive transform data from the socket
    bool timeout(false);
    socket->Receive(statusMsg->GetPackBodyPointer(), statusMsg->GetPackBodySize(), timeout);

    // Deserialize the transform data
    // If you want to skip CRC check, call Unpack() without argument.

    int c = statusMsg->Unpack(1);

    if (statusMsg->GetSubCode() != 2687068)
    {
        std::cout << "\n---> Received statusMessage from Slicer: " << statusMsg->GetStatusString() << std::endl;

        if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
        {
            // std::cerr << "========== STATUS ==========" << std::endl;
            // std::cerr << " Code      : " << statusMsg->GetCode() << std::endl;
            // std::cerr << " SubCode   : " << statusMsg->GetSubCode() << std::endl;
            // std::cerr << " Error Name: " << statusMsg->GetErrorName() << std::endl;
            // std::cerr << " Status    : " << statusMsg->GetStatusString() << std::endl;
            // std::cerr << "============================" << std::endl << std::endl;

            // Modify global variables with status received    
            Global::globalArgCode = statusMsg->GetCode();
            Global::globalArgSubcode = statusMsg->GetSubCode();
            Global::globalArgErrorName = statusMsg->GetErrorName();
            Global::globalArgStatusStringMessage = statusMsg->GetStatusString();
            Global::globalDeviceName = header->GetDeviceName();
            return 1;
        }
    }

    return 0;

}


int ReceiveTransform(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{
    std::cout << "\n---> Received transformMessage from Slicer." << std::endl;

    // Create a message buffer to receive transform datag
    igtl::TransformMessage::Pointer transMsg;
    transMsg = igtl::TransformMessage::New();
    transMsg->SetMessageHeader(header);
    transMsg->AllocatePack();

    // Receive transform data from the socket
    bool timeout(false);
    socket->Receive(transMsg->GetPackBodyPointer(), transMsg->GetPackBodySize(), timeout);

    // Deserialize the transform data
    // If you want to skip CRC check, call Unpack() without argument.
    int c = transMsg->Unpack(1);

    if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
    {
        // Retrive the transform data
        igtl::Matrix4x4 matrix;
        transMsg->GetMatrix(matrix);
        //igtl::PrintMatrix(matrix);
        std::cerr << std::endl;

        //Global::globalMatrix = matrix;
        memcpy(Global::globalMatrix, matrix, sizeof(matrix));
        Global::globalDeviceName = header->GetDeviceName();

        //TransformReceived = 1;
        return 1;
    }
  return 0;
}
