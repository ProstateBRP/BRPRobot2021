#include <iostream>
#include <math.h>
#include <cstdlib>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlServerSocket.h"

#define N_STRINGS 5
#define START_BUTTON_ON 1
#define START_BUTTON_OFF 0

const char * testString[N_STRINGS] = {
  "OpenIGTLink",
  "Networkokokok",
  "Communication",
  "SALUUUUUT",
  "Image Guided Therapy",
};


int main(int argc, char* argv[])
{
    if (argc != 4) // check number of arguments
    {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <port> <fps> <start_button 0 or 1>"    << std::endl;
    std::cerr << "    <port>     : Port # (18944 in Slicer default)"   << std::endl;
    std::cerr << "    <fps>      : Frequency (fps) to send string" << std::endl;
    std::cerr << "    <start_button>      : if the start_button is on (1) or off (0)" << std::endl;
    exit(0);
    }

    int    port     = atoi(argv[1]);
    double fps      = atof(argv[2]);
    int    interval = (int) (1000.0 / fps);
    bool   start_button = atoi(argv[3]);

    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();
    stringMsg->SetDeviceName("StringMessage");

    igtl::ServerSocket::Pointer serverSocket;
    serverSocket = igtl::ServerSocket::New();
    int r = serverSocket->CreateServer(port);

    if (r < 0)
    {
        std::cerr << "Cannot create a server socket." << std::endl;
        exit(0);
    }

    igtl::Socket::Pointer socket;

    

    if(start_button == START_BUTTON_ON)
    {
        while(1)
        {
            // Waiting for Connection

            socket = serverSocket->WaitForConnection(1000);
            std::cout << "Socket value string: " << socket << std::endl;

            if (socket.IsNotNull()) // if client connected
            {

                //std::cout << "Sending string: " << testString[1] << std::endl;
                std::cout << "Sending string: " << "CMD_0001" << std::endl;
                stringMsg->SetDeviceName("StringMessage");
                //stringMsg->SetString(testString[1]);
                stringMsg->SetString("CMD_0001");
                stringMsg->Pack();
                socket->Send(stringMsg->GetPackPointer(), stringMsg->GetPackSize());
                igtl::Sleep(interval); // wait
            }
        }
    }
    else
    {
        std::cerr << "Start button no pressed" << std::endl;
        exit(0);
    }
  
    //Sending STRING( CMD_0001, START_UP )

}
