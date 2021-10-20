
#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"

#include "LisaScript.h"

#define FPS  10
#define interval 100

void startup()
{
    return 1;
}
   
int getStatus()
{
    return 1;
}



void SendStringToSlicer(char*  hostname, int port, char*  argDeviceName,char*  argMessage)
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


    while (1)
    {
            stringMsg->SetDeviceName(argDeviceName); 
            std::cout << "Sending string: " << argMessage << std::endl;
            stringMsg->SetString(argMessage);
            stringMsg->Pack();
            socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());     
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