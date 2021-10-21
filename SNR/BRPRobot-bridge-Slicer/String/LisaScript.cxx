
#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include "igtlClientSocket.h"

#include "LisaScript.hxx"

#define FPS  10
#define interval 100

   
int getStatus()
{
    return 1;
}


// Function to send a String to Slicer 

void SendStringToSlicer(char*  hostname, int port, char* argDeviceName,char* argMessage)
{
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

    //------------------------------------------------------------
    // Allocate Transform Message Class

    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();
    //------------------------------------------------------------
    // loop

    //while (1)
    int i = 0;
    while (i == 0)
    {
        stringMsg->SetDeviceName(argDeviceName); 
        stringMsg->SetString(argMessage);
        stringMsg->Pack();
        socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());
        std::cout << "Sending STRING: " << argMessage << std::endl;
        i = 1;     
     }

}

// Function to send a status to Slicer 
void SendStatusToSlicer(char*  hostname, int port, char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage)
{
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

    //------------------------------------------------------------
    // Allocate Status Message Class

    igtl::StatusMessage::Pointer statusMsg;
    statusMsg = igtl::StatusMessage::New();
    statusMsg->SetDeviceName(argDeviceName);
    //------------------------------------------------------------
    // loop

    int i = 0;
    while (i == 0)
    {
        statusMsg->SetCode(argCode);
        statusMsg->SetSubCode(argSubcode);
        statusMsg->SetErrorName(argErrorName);
        statusMsg->SetStatusString(argStatusStringMessage);
        statusMsg->Pack();
        socket->Send(statusMsg->GetPackPointer(), statusMsg->GetPackSize());
        std::cout << "Sending STATUS: " << statusMsg << std::endl;
        i = 1;
     }
}


void SendTransformToSlicer(const char* hostname, int port, char* argDeviceName, igtl::Matrix4x4& matrix)
{
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

    //------------------------------------------------------------
    // Allocate Transform Message Class
  
    igtl::TransformMessage::Pointer transMsg;
    transMsg = igtl::TransformMessage::New();
    transMsg->SetDeviceName(argDeviceName);

    std::cout << "Sending TRANSFORM" << std::endl;

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


/*
int ReceiveString(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{
  std::cerr << "Receiving STRING data type." << std::endl;
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
  if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
    {
    std::cerr << "Encoding: " << stringMsg->GetEncoding() << "; "
              << "String: " << stringMsg->GetString() << std::endl << std::endl;
    }
  return 1;
}
*/
