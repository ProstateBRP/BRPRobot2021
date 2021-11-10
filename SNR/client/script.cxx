
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

// Set default values for the hostname and port (to be updated by a function call to setSocketVars)
char * Global::hostname = (char*)"localhost";
int Global::port = 18944;

bool Global::testRunning = true;

//std::string Global::past_globalString = "DefaultPastString";
std::string Global::globalString = "DefaultGlobalString";
std::string Global::globalDeviceName = "DefaultGlobalDeviceName";
//std::string Global::globalEncoding = "DefaultGlobalEncoding";

int Global::globalArgCode = 0;
int Global::globalArgSubcode = 0;
std::string Global::globalArgErrorName = "DefaultGlobalArgErrorName";
std::string Global::globalArgStatusStringMessage = "DefaultArgStatusStringMessage";


#ifdef MAIN

int main(int argc, char* argv[])
{

    if (argc != 7) // check number of arguments
    {
        // If not correct, print usage
        std::cerr << "Usage: " << argv[0] << " <message> <argCode> <argSubcode> <argErrorName><argStatusStringMessage> <boolSending> "    << std::endl;
        std::cerr << "    <message>     : string message to be sent to slicer, write anything is no message has to be sent" << std::endl;
        std::cerr << "    <argCode>     : 1" << std::endl;
        std::cerr << "    <argSubcode>     : 128" << std::endl;
        std::cerr << "    <argErrorName>     : OK!" << std::endl;
        std::cerr << "    <argStatusStringMessage>     : This is a test to send status message." << std::endl;
        std::cerr << "    <boolSending>     : Must be 1 to send messages to Slicer and 0 to receive from Slicer." << std::endl;
        exit(0);
    }

    char*  argMessage = argv[1]; 
    unsigned short argCode = atoi(argv[2]);
    unsigned  long  long argSubcode = atoi(argv[3]);
    char* argErrorName = argv[4];
    char* argStatusStringMessage = argv[5];
    bool boolSending = atoi(argv[6]);
    char *deviceName1 = (char *)("StringMessage");
    char *deviceName2 = (char *)("StatusMessage");
    char *deviceName3 = (char *)("TransformMessage");
    

    // Matrix defined for testing transform exchange
    float inT[4] = {-0.954892f, 0.196632f, -0.222525f, 0.0};
    float inS[4] = {-0.196632f, 0.142857f, 0.970014f, 0.0};
    float inN[4] = {0.222525f, 0.970014f, -0.0977491f, 0.0};
    float inOrigin[4] = {46.0531f,19.4709f,46.0531f, 1.0};
    igtl::Matrix4x4 inMatrix = {{inT[0],inS[0],inN[0],inOrigin[0]},
                            {inT[1],inS[1],inN[1],inOrigin[1]},
                            {inT[2],inS[2],inN[2],inOrigin[2]},
                            {inT[3],inS[3],inN[3],inOrigin[3]}};

        // Matrix2 defined for testing transform exchange
    float inT2[4] = {-2.954892f, 3.196632f, -4.222525f, 2.0};
    float inS2[4] = {-2.196632f, 3.142857f, 4.970014f, 2.0};
    float inN2[4] = {2.222525f, 3.970014f, -4.0977491f, 2.0};
    float inOrigin2[4] = {46.0531f,19.4709f,46.0531f, 3.0};
    igtl::Matrix4x4 inMatrix2 = {{inT2[0],inS2[0],inN2[0],inOrigin2[0]},
                            {inT2[1],inS2[1],inN2[1],inOrigin2[1]},
                            {inT2[2],inS2[2],inN2[2],inOrigin2[2]},
                            {inT2[3],inS2[3],inN2[3],inOrigin2[3]}};



    if(boolSending == 0)
    {
        // Other implementation

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
        // Wait for Slicer to send something

        bool Received = 0;
        // loop
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
            Received = 1;
            // std::cout << "String received from Slicer : " << Global::globalString << std::endl; 
            // std::cout << "String encoding received from Slicer : " << Global::globalEncoding << std::endl; 
            }
            else if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
            {
            ReceiveStatus(socket, headerMsg);
            //std::cout << "Receiving status from Slicer " << headerMsg <<std::endl;
            Received = 1;
            }
            else if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
            {
            ReceiveTransform(socket, headerMsg);
            Received = 1;
            }
        }     
    }
    else
    {
        SendStringToSlicer(deviceName1, argMessage);
        //SendStringToSlicer(deviceName1, "Lemessagedeux");
        //SendStateToSlicer(deviceName2,argCode,argSubcode, argErrorName,argStatusStringMessage);
        //SendTransformToSlicer(deviceName3, inMatrix);
        //SendTransformToSlicer(deviceName3, inMatrix2);
    }
    
}


#else

#endif




void setSocketVars(char* snrHostname, int snrPort)
{
    Global::hostname = snrHostname;
    Global::port = snrPort;
}

void *startThread(void *ptr)
{
    std::cout << "\n---> Starting thread in script.cxx to receive messages from Slicer." << std::endl;
    // Create thread for the receiving function
    pthread_t thread;
    pthread_create(&thread, NULL, receivingFunction, NULL);

    //pthread_exit(NULL);
    return NULL;
}

// another function here that is continuously run by the thread
void *receivingFunction(void *ptr)
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
        // Received = 1;
        // std::cout << "String received from Slicer : " << Global::globalString << std::endl; 
        // std::cout << "String encoding received from Slicer : " << std::to_string(Global::globalEncoding) << std::endl; 
        }
        else if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
        {
        ReceiveStatus(socket, headerMsg);
        std::cout << "Receiving status from Slicer " << headerMsg <<std::endl;
        // Received = 1;
        }
        else if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
        {
        ReceiveTransform(socket, headerMsg);
        // Received = 1;
        }
    } 
    return NULL;
}


void SendStringToSlicer(char* argDeviceName, char* argMessage)
{
    // //------------------------------------------------------------
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
    std::cout << "Sending stringMessage from script.cxx to Slicer: " << argMessage << std::endl;

}

void SendStateToSlicer(char *argDeviceName, unsigned short argCode, unsigned long long argSubcode, char *argErrorName, char *argStatusStringMessage)
{
    // //------------------------------------------------------------
    // // Establish Connection

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
        std::cout << "Sending statusMessage from script.cxx to Slicer:\n" << statusMsg << std::endl;
        i = 1;
    }
}

void SendTransformToSlicer(char *argDeviceName, igtl::Matrix4x4 &matrix, char * wpiDeviceName)
{
    // Send TransformInfo to Slicer
    char *deviceName4 = (char *)("TransformMessage");
    SendStringToSlicer(deviceName4, wpiDeviceName);
    // //------------------------------------------------------------
    // // Establish Connection

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
    
    std::cout << "Sending transformMessage from script.cxx to Slicer:" << std::endl;

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
    // //------------------------------------------------------------
    // // Establish Connection

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
      //if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
      //{

        ReceiveString(socket, headerMsg);
        StringReceived = 1;
        std::cout << "StringMessage received in script.cxx from Slicer : " << Global::globalString << std::endl; 
        //std::cout << "StringEncoding received in script.cxx from Slicer : " << Global::globalEncoding << std::endl; 
        std::cout << "Current deviceName : " << Global::globalDeviceName << std::endl;
      //}
    }     
 }

void GetStateFromSlicer(const char* hostname, int port)
{

    // //------------------------------------------------------------
    // // Establish Connection

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


      //if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
      //{
        ReceiveStatus(socket, headerMsg);
        std::cout << "inside GetStateFromSlicer " << headerMsg <<std::endl;
        StatusReceived = 1;
      //}
    }     
 }

void GetTransformFromSlicer(const char* hostname, int port)
{

    // //------------------------------------------------------------
    // // Establish Connection

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


      //if (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0)
      //{
        ReceiveTransform(socket, headerMsg);
        TransformReceived = 1;
      //}
    }     
 }

int ReceiveString(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{

    std::cerr << "\n---> Receiving StringMessage in script.cxx from Slicer." << std::endl;

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
              << "String: " << stringMsg->GetString() << std::endl;
    }
    Global::globalString = stringMsg->GetString();
    Global::globalDeviceName = header->GetDeviceName();
    //Global::globalEncoding = stringMsg->GetEncoding();

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

        // Modify global variables with status received    
        Global::globalArgCode = statusMsg->GetCode();
        Global::globalArgSubcode = statusMsg->GetSubCode();
        Global::globalArgErrorName = statusMsg->GetErrorName();
        Global::globalArgStatusStringMessage = statusMsg->GetStatusString();
    }

    return 0;

}


int ReceiveTransform(igtl::Socket * socket, igtl::MessageHeader::Pointer& header)
{
    //bool TransformReceived = 0;
    std::cerr << "Receiving TRANSFORM data type." << std::endl;
    //while(TransformReceived == 0)
    //{
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
    std::cout << "inside Transform " <<std::endl;
    if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
    {
        std::cout << "inside GetTransformFromSlicer " <<std::endl;
        // Retrive the transform data
        igtl::Matrix4x4 matrix;
        transMsg->GetMatrix(matrix);
        igtl::PrintMatrix(matrix);
        std::cerr << std::endl;
        //TransformReceived = 1;
        return 1;
    }
  return 0;
}
