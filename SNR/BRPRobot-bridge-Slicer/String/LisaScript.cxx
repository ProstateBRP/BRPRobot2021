
#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include "igtlClientSocket.h"

#include "LisaScript.h"

#define FPS  10
#define interval 100

int getStatus()
{
    return 1;
}

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

    // Send string message

    stringMsg->SetDeviceName(argDeviceName); 
    stringMsg->SetString(argMessage);
    stringMsg->Pack();
    socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());
    std::cout << "Sending STRING: " << argMessage << std::endl;

}



void SendStateToSlicer(char*  hostname, int port, char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage)
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


void GetStringFromSlicer(const char* hostname, int port)
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
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();
    bool messageReceived = 0;

    while(messageReceived == 0)
    {
    // Message is a StringMessage
      if ( strcmp(headerMsg->GetDeviceType(), "STRING") == 0 )
      {
        igtl::StringMessage::Pointer strMsg(igtl::StringMessage::New());
        strMsg->SetMessageHeader(headerMsg);
        strMsg->AllocatePack();
        bool timeout = false;
        socket->Receive(strMsg->GetPackBodyPointer(), strMsg->GetPackBodySize(), timeout);
        int c = strMsg->Unpack();

        // Echo message back
        strMsg->SetDeviceName("StringEchoClient");
        strMsg->Pack();
        socket->Send(strMsg->GetPackPointer(), strMsg->GetPackSize());

        char* message = (char*)(strMsg->GetString());
        messageReceived = 1;
      }
        socket->CloseSocket();
    }

}

void GetStateFromSlicer(const char* hostname, int port)
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
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();
    bool messageReceived = 0;
    while(messageReceived == 0)
    {
    // Message is a StringMessage
      if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
      {
        igtl::StatusMessage::Pointer statusMsg;
        statusMsg = igtl::StatusMessage::New();
        statusMsg->SetMessageHeader(headerMsg);
        statusMsg->AllocatePack();
        bool timeout = false;
        socket->Receive(statusMsg->GetPackBodyPointer(), statusMsg->GetPackBodySize(), timeout);

        unsigned short argCode = statusMsg->GetCode();
        unsigned long long argSubcode = statusMsg->GetSubCode();
        char* argErrorName = (char*)(statusMsg->GetErrorName());
        char* argStatusStringMessage = (char*)(statusMsg->GetStatusString());
        
        messageReceived = 1;
      }
    }
}

void GetTransformFromSlicer(const char* hostname, int port)
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
    // Create a message buffer to receive header

    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();

    // Receive Transform message
    bool messageReceived = 0;
    while(messageReceived == 0)
    {
    // Message is a Transform message

      if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
      {
        igtl::TransformMessage::Pointer transMsg;
        transMsg = igtl::TransformMessage::New();
        transMsg->SetMessageHeader(headerMsg);
        transMsg->AllocatePack();
        bool timeout = false;
        socket->Receive(transMsg->GetPackBodyPointer(), transMsg->GetPackBodySize(), timeout);

        int c = transMsg->Unpack(1);
        if (c & igtl::MessageHeader::UNPACK_BODY) 
        {
          // if CRC check is OK. Read transform data.
          igtl::Matrix4x4 matrix;
          transMsg->GetMatrix(matrix);
          igtl::PrintMatrix(matrix);

        }
        messageReceived = 1;
      }
    }

}

