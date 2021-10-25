
#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include "igtlClientSocket.h"

#include "script.hxx"

#define FPS 200
#define interval 5

int getStatus()
{
    return 1;
}
//std::string Global::myglobalstring = "DefaultGlobalString";


#ifdef MAIN

int main(int argc, char* argv[])
{

    if (argc != 9) // check number of arguments
    {
        // If not correct, print usage
        std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>"    << std::endl;
        std::cerr << "    <hostname>    : IP or host name"                    << std::endl;
        std::cerr << "    <port>        : Port # (18944 in Slicer default)"   << std::endl;
        std::cerr << "    <devicename>  : Name of the device " << std::endl;
        std::cerr << "    <message>     : string message to be sent to slicer, write anything is no message has to be sent" << std::endl;
        std::cerr << "    <argCode>     : STATUS_OK" << std::endl;
        std::cerr << "    <argSubcode>     : 128" << std::endl;
        std::cerr << "    <argErrorName>     : OK!" << std::endl;
        std::cerr << "    <argStatusStringMessage>     : This is a test to send status message." << std::endl;
        exit(0);
    }

    char* hostname = argv[1];
    int port = atoi(argv[2]);
    char* argDeviceName = argv[3];
    char*  argMessage = argv[4]; 
    unsigned short argCode = atoi(argv[5]);
    unsigned  long  long argSubcode = atoi(argv[6]);
    char* argErrorName = argv[7];
    char* argStatusStringMessage = argv[8];

    // Matrix defined for testing transform exchange
    float inT[4] = {-0.954892f, 0.196632f, -0.222525f, 0.0};
    float inS[4] = {-0.196632f, 0.142857f, 0.970014f, 0.0};
    float inN[4] = {0.222525f, 0.970014f, -0.0977491f, 0.0};
    float inOrigin[4] = {46.0531f,19.4709f,46.0531f, 1.0};
    igtl::Matrix4x4 inMatrix = {{inT[0],inS[0],inN[0],inOrigin[0]},
                            {inT[1],inS[1],inN[1],inOrigin[1]},
                            {inT[2],inS[2],inN[2],inOrigin[2]},
                            {inT[3],inS[3],inN[3],inOrigin[3]}};

    //std::cout << "Global value before function is : " << myglobalint << std::endl;
    
    //std::cout << "Global string before function is: " << Global::myglobalstring << std::endl;

    SendStringToSlicer(hostname, port, argDeviceName, argMessage);
    
    //SendStringToSlicer(hostname, port, "Device2", "Saluuut");

   



    //SendStateToSlicer(hostname, port, argDeviceName,argCode,argSubcode, argErrorName,argStatusStringMessage);
/*
    SendTransformToSlicer(hostname, port, argDeviceName, inMatrix);*/
    //int myglobalint = 44;

   

    GetStringFromSlicer(hostname, port);
  
   
    //GetStateFromSlicer(hostname, port);
    //GetTransformFromSlicer(hostname, port);

    
}



#else

#endif
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

void SendStateToSlicer(char *hostname, int port, char *argDeviceName, unsigned short argCode, unsigned long long argSubcode, char *argErrorName, char *argStatusStringMessage)
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

void SendTransformToSlicer(const char *hostname, int port, char *argDeviceName, igtl::Matrix4x4 &matrix)
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

    //------------------------------------------------------------
    // Wait for String message from Slicer until it sends one string message
    std::cout << "inside GetSTringFromSlicer debut " <<std::endl;
    bool StringReceived = 0;
    // loop
    while (StringReceived == 0)
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
        StringReceived = 1;
        std::cout << "String received from Slicer : " << Global::myglobalstring << std::endl; 
      }
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


      if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
      {
        ReceiveStatus(socket, headerMsg);
        std::cout << "inside GetStateFromSlicer " << headerMsg <<std::endl;
        StatusReceived = 1;
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


      if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
      {
        ReceiveTransform(socket, headerMsg);
        TransformReceived = 1;
      }
    }     
 }

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
     
     Global::myglobalstring = stringMsg->GetString();

  return 1;
}


int ReceiveStatus(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{

  std::cerr << "Receiving STATUS data type." << std::endl;

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

  if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
    {
    std::cerr << "========== STATUS ==========" << std::endl;
    std::cerr << " Code      : " << statusMsg->GetCode() << std::endl;
    std::cerr << " SubCode   : " << statusMsg->GetSubCode() << std::endl;
    std::cerr << " Error Name: " << statusMsg->GetErrorName() << std::endl;
    std::cerr << " Status    : " << statusMsg->GetStatusString() << std::endl;
    std::cerr << "============================" << std::endl << std::endl;
    }

  return 0;

}


int ReceiveTransform(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{
  bool TransformReceived = 0;
  std::cerr << "Receiving TRANSFORM data type." << std::endl;
  while(TransformReceived == 0)
  {
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
    std::cout << "inside GetTransformFromSlicer " <<std::endl;
    // Retrive the transform data
    igtl::Matrix4x4 matrix;
    transMsg->GetMatrix(matrix);
    igtl::PrintMatrix(matrix);
    std::cerr << std::endl;
    TransformReceived = 1;
    return 1;
    
    }
   }
  return 0;
}
