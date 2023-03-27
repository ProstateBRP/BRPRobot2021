#include "OpenIGTLink.h"

// Constructor
OpenIGTLink::OpenIGTLink(Robot *robot, int port)
{
    this->robot = robot;

    // Port used for communication
    this->port = port;

    // On new connections retransmit robot state
    retransmit = false;

    // Does the client have a keep alive functionality ?
    keepAlive = false;
}

void *OpenIGTLink::ThreadIGT(void *igt)
{
    //------------------------------------------------------------
    // Setup workphases
    OpenIGTLink *igtModule = (OpenIGTLink *)igt;

    igtModule->WorkphaseList.push_back(new RobotUndefinedPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotStartUpPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotPlanningPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotCalibrationPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotTargetingPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotMoveToTargetPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotManualPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotStopPhase(igtModule->robot));
    igtModule->WorkphaseList.push_back(new RobotEmergencyPhase(igtModule->robot));

    igtl::ServerSocket::Pointer serverSocket;
    serverSocket = igtl::ServerSocket::New();
    int r = serverSocket->CreateServer(igtModule->port);

    if (r < 0)
    {
        std::cerr << "ERROR: Cannot create a server socket." << std::endl;
        exit(0);
    }
    // While we are listening on this port
    while (1)
    {
        //------------------------------------------------------------
        // Waiting for Connection
        igtModule->socket = serverSocket->WaitForConnection(2000);
        // std::cout << "waiting for connection\n";

        // Connection specific variables state -- Not connected, This will show up in the UI console
        igtModule->clientSocketConnected = 0;

        if (igtModule->socket.IsNotNull()) // if client connected
        {
            // Connection Specific Variables State -- Connected
            igtModule->clientSocketConnected = -1;

            std::cerr << "MESSAGE: Client connected. Starting a session..." << std::endl;
            igtModule->Session();
        }
        // Socket closed change connect to listening
        igtModule->clientSocketConnected = 0;
    }

    //------------------------------------------------------------
    // Close connection
    igtModule->socket->CloseSocket();
    return NULL;
}

int OpenIGTLink::Session()
{
    // Set socket and robot status
    std::vector<RobotPhaseBase *>::iterator iter;
    for (iter = WorkphaseList.begin(); iter != WorkphaseList.end(); iter++)
    {
        // std::cerr << "MESSAGE: Setting up " << (*iter)->Name() << " phase." << std::endl;
        (*iter)->SetSocket(socket);
        (*iter)->connect = true;
    }

    //------------------------------------------------------------
    // Set undefined phase as the current phase;
    std::vector<RobotPhaseBase *>::iterator currentPhase = WorkphaseList.begin();
    // Update robot state
    robot->SetCurrentState((*currentPhase)->Name());
    //------------------------------------------------------------
    // loop
    while ((*currentPhase)->connect)
    {
        // Statement will change the state upon request of a new state.
        if ((*currentPhase)->Process())
        {
            std::string requestedWorkphase = (*currentPhase)->GetNextWorkPhase();
            std::string queryID = (*currentPhase)->GetQueryID();

            // Find the requested workphase
            std::vector<RobotPhaseBase *>::iterator iter;
            for (iter = WorkphaseList.begin(); iter != WorkphaseList.end(); iter++)
            {
                if (strcmp((*iter)->Name(), requestedWorkphase.c_str()) == 0)
                {
                    // Perform state-specific cleanup
                    (*currentPhase)->OnExit();
                    // Change the current phase
                    currentPhase = iter;
                    (*currentPhase)->Enter(queryID.c_str()); // Initialization process
                                                             // Update robot current state
                    robot->SetCurrentState((*currentPhase)->Name());
                    break;
                }
            }
        }
    }
    robot->Reset();
    return 1;
}
void OpenIGTLink::DisconnectSocket()
{
    socket->CloseSocket();
}
