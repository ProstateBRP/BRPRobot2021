/*=========================================================================
// To modify
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
// Add a LisaClient.h file

#include <iostream>
#include <math.h>
#include <cstdlib>
#include <string>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"


// Check if all needed
#include <iomanip>

#include "igtlMessageHeader.h"
#include "igtlTransformMessage.h"
#include "igtlStringMessage.h"

// Functions declarations

int ReceiveTransform(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
int ReceiveStatus(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
int ReceiveString(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);


int main(int argc, char* argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

    if (argc != 6) // check number of arguments
    {
        // If not correct, print usage
        std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>"    << std::endl;
        std::cerr << "    <hostname>    : IP or host name"                    << std::endl;
        std::cerr << "    <port>        : Port # (18944 in Slicer default)"   << std::endl;
        std::cerr << "    <fps>         : Frequency (fps) to send string" << std::endl;
        std::cerr << "    <messagetype> : Type of the message (SEND_STRING,SEND_STATE,SEND_TRANSFORM,GET_STRING,GET_STATE,GET_TRANSFORM)" << std::endl;
        //std::cerr << "    <devicename>  : Name of the device " << std::endl;
        std::cerr << "    <message>     : string message to be sent to slicer, write anything is no message has to be sent" << std::endl;
        exit(0);
    }

    char*  hostname = argv[1];
    int    port     = atoi(argv[2]);
    double fps      = atof(argv[3]);
    int    interval = (int) (1000.0 / fps);
    char*  argMessageType = argv[4];
    //char*  argDeviceName = argv[5];
    char*  argMessage = argv[5];
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

    // Define Device name

    std::string argDeviceName = "WednesdayDevice"; // hardcoded device name 

    //------------------------------------------------------------
    // Allocate Transform Message Class

    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();

    //------------------------------------------------------------
    // Allocate Status Message Class

    igtl::StatusMessage::Pointer statusMsg;
    statusMsg = igtl::StatusMessage::New();
    statusMsg->SetDeviceName(argDeviceName);

    //------------------------------------------------------------
    // Create a message buffer to receive header
    igtl::MessageHeader::Pointer headerMsg;
    headerMsg = igtl::MessageHeader::New();

    //------------------------------------------------------------
    // Allocate a time stamp
    igtl::TimeStamp::Pointer ts;
    ts = igtl::TimeStamp::New();

    //------------------------------------------------------------
    // loop


    while (1)
    {
        const char *str_inp1="SEND_STRING";
        const char *str_inp2="SEND_STATE";
        const char *str_inp3="SEND_TRANSFORM";
        const char *str_inp4="GET_STRING";
        const char *str_inp5="GET_STATE";
        const char *str_inp6="GET_TRANSFORM";
        

        if(strcmp(argMessageType, str_inp1) == 0)
        {
            stringMsg->SetDeviceName(argDeviceName); 
            std::cout << "Sending string: " << argMessage << std::endl;
            stringMsg->SetString(argMessage);
            stringMsg->Pack();
            socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());     
        }
        else if(strcmp(argMessageType, str_inp2) == 0)
        {
            statusMsg->SetCode(igtl::StatusMessage::STATUS_OK);
            statusMsg->SetSubCode(128);
            statusMsg->SetErrorName("OK!");
            statusMsg->SetStatusString("This is a test to send status message.");
            statusMsg->Pack();
            socket->Send(statusMsg->GetPackPointer(), statusMsg->GetPackSize());
            std::cout << "Sending STATUS: " << statusMsg << std::endl;
        }
        else if (strcmp(argMessageType, str_inp3) == 0)
        {
            std::cout << "We are in Transform case" <<  std::endl;
        }

        else if((strcmp(argMessageType, str_inp4) == 0)||(strcmp(argMessageType, str_inp5) == 0) ||(strcmp(argMessageType, str_inp6) == 0))
                {
                    for (int i = 0; i < 100; i ++)
                    {
                        // Initialize receive buffer
                        headerMsg->InitPack();

                        // Receive generic header from the socket
                        bool timeout(false);
                        igtlUint64 r = socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize(), timeout);

                        if (r != headerMsg->GetPackSize())
                        {
                          continue;
                        }

                        // Deserialize the header
                        headerMsg->Unpack();

                        // Get time stamp
                        igtlUint32 sec;
                        igtlUint32 nanosec;

                        headerMsg->GetTimeStamp(ts);
                        ts->GetTimeStamp(&sec, &nanosec);

                        std::cerr << "Name: " << headerMsg->GetDeviceName() << std::endl;
                        std::cerr << "Time stamp: "
                                   << sec << "." << std::setw(9) << std::setfill('0')
                                   << nanosec << std::endl;


                        // Check data type and receive data body

                        if ((strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)&&(strcmp(argMessageType, str_inp6) == 0)) // Change order to make it consistent 
                        {
                            ReceiveTransform(socket, headerMsg);
                        }
                
                        else if ((strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)&&(strcmp(argMessageType, str_inp5) == 0))
                        {
                            ReceiveStatus(socket, headerMsg);
                        }
                        else if ((strcmp(headerMsg->GetDeviceType(), "STRING") == 0)&&(strcmp(argMessageType, str_inp4) == 0))
                        {
                           ReceiveString(socket, headerMsg);
                        }
                        else
                        {
                            std::cerr << "Receiving : " << headerMsg->GetDeviceType() << std::endl;
                            //std::cerr << "This type of message:" << argMessageType << " is not supported." << std::endl;
                            socket->Skip(headerMsg->GetBodySizeToRead(), 0);
                        }
                    }
                }

              /* else if (strcmp(argMessageType, str_inp4) == 0)
                 {
                    std::cout << "We are in GET_STRING case" <<  std::endl;
                 }
                
                else if (strcmp(argMessageType, str_inp5) == 0)
                {
                    std::cout << "We are in GET_STATE case" <<  std::endl;
                }
                else if (strcmp(argMessageType, str_inp6) == 0)
                {
                    std::cout << "We are in GET_TRANSFORM case" <<  std::endl;
                }
                else
                {
                    std::cerr << "This type of message:" << argMessageType << " is not supported." << std::endl; // Add the print of message type 
                    exit(0);
                }
                    */

        
        igtl::Sleep(interval); // wait
    }

    //------------------------------------------------------------
    // Close connection

    socket->CloseSocket();
}


// Functions definitions


int ReceiveTransform(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{
  std::cerr << "Receiving TRANSFORM data type." << std::endl;

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
    igtl::PrintMatrix(matrix);
    std::cerr << std::endl;
    return 1;
    }

  return 0;
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

