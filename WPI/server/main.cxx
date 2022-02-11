/*=========================================================================

  Program:   BRP Prostate Robot: Testing  (Server)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#include <iostream>
#include <iomanip>
#include <math.h>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

//#include "igtlOSUtil.h"
//#include "igtlMessageHeader.h"
//#include "igtlTransformMessage.h"
//#include "igtlImageMessage.h"
#include "igtlServerSocket.h"
//#include "igtlStatusMessage.h"
//#include "igtlPositionMessage.h"
//#include "igtlPointMessage.h"
//#include "igtlStringMessage.h"
//#include "igtlBindMessage.h"

#include "RobotPhaseBase.h"
#include "RobotUndefinedPhase.h"
#include "RobotStartUpPhase.h"
#include "RobotPlanningPhase.h"
#include "RobotCalibrationPhase.h"
#include "RobotTargetingPhase.h"
#include "RobotMoveToTargetPhase.h"
#include "RobotManualPhase.h"
#include "RobotStopPhase.h"
#include "RobotEmergencyPhase.h"
#include "RobotStatus.h"
#include "../Utilities/Logger/Logger.hpp"
typedef std::vector<RobotPhaseBase *> WorkphaseList;

int Session(igtl::Socket *socket, WorkphaseList &wlist);

int main(int argc, char *argv[])
{
    Logger &log = Logger::GetInstance();

    //------------------------------------------------------------
    // Setup workphases
    WorkphaseList wlist;
    wlist.push_back(new RobotUndefinedPhase);
    wlist.push_back(new RobotStartUpPhase);
    wlist.push_back(new RobotPlanningPhase);
    wlist.push_back(new RobotCalibrationPhase);
    wlist.push_back(new RobotTargetingPhase);
    wlist.push_back(new RobotMoveToTargetPhase);
    wlist.push_back(new RobotManualPhase);
    wlist.push_back(new RobotStopPhase);
    wlist.push_back(new RobotEmergencyPhase);

    std::cerr << std::endl;

    //------------------------------------------------------------
    // Parse Arguments
    if (argc < 2) // check number of arguments
    {
        // If not correct, print usage
        std::cerr << "Usage: " << argv[0] << "<port>" << std::endl;
        std::cerr << "    <port>     : Port # (18944 in Slicer default)" << std::endl;
        exit(0);
    }

    int port = atoi(argv[1]);

    igtl::ServerSocket::Pointer serverSocket;
    serverSocket = igtl::ServerSocket::New();
    int r = serverSocket->CreateServer(port);

    if (r < 0)
    {
        std::cerr << "ERROR: Cannot create a server socket." << std::endl;
        exit(0);
    }

    igtl::Socket::Pointer socket;

    while (1)
    {
        //------------------------------------------------------------
        // Waiting for Connection
        socket = serverSocket->WaitForConnection(2000);
        std::cout << "waiting for connection\n";

        if (socket.IsNotNull()) // if client connected
        {
            std::cerr << "MESSAGE: Client connected. Starting a session..." << std::endl;
            Session(socket, wlist);
        }
    }

    //------------------------------------------------------------
    // Close connection (The example code never reaches to this section ...)
    socket->CloseSocket();
    return 0;
}
/*******************************************************************************************/
/*************************************Methods***********************************************/
/*******************************************************************************************/

int Session(igtl::Socket *socket, WorkphaseList &wlist)
{
    RobotStatus *rs = new RobotStatus();

    //------------------------------------------------------------
    // Set socket and robot status
    std::vector<RobotPhaseBase *>::iterator iter;
    for (iter = wlist.begin(); iter != wlist.end(); iter++)
    {
        // std::cerr << "MESSAGE: Setting up " << (*iter)->Name() << " phase." << std::endl;
        (*iter)->SetSocket(socket);
        (*iter)->SetRobotStatus(rs);
        (*iter)->connect = 1;
    }

    //------------------------------------------------------------
    // Set undefined phase as the current phase;
    std::vector<RobotPhaseBase *>::iterator currentPhase = wlist.begin();
    //------------------------------------------------------------
    // loop
    while ((*currentPhase)->connect)
    {
        // This statement checks for workphase change request
        // If no workphase change has requested the process will take care of the received message
        if ((*currentPhase)->Process())
        {
            // If Process() returns 1, phase change has been requested.
            std::string requestedWorkphase = (*currentPhase)->GetNextWorkPhase();
            std::string queryID = (*currentPhase)->GetQueryID();

            // Find the requested workphase
            std::vector<RobotPhaseBase *>::iterator iter;
            for (iter = wlist.begin(); iter != wlist.end(); iter++)
            {
                if (strcmp((*iter)->Name(), requestedWorkphase.c_str()) == 0)
                {
                    // Change the current phase
                    currentPhase = iter;
                    (*currentPhase)->Enter(queryID.c_str()); // Initialization process
                    break;
                }
            }
        }
    }

    return 1;
}
