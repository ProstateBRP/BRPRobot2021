//============================================================================
// Name        : SurgicalRobot.cpp
// Author      : Produced in the WPI AIM Lab
// Description : This file is where the code starts via the main function.
//				 It includes initializing the menu and setting up the system.
//============================================================================

#include <utility>
#include <memory>
#include <iostream>
#include <stdio.h>
#include <string.h>
#include <iostream>
#include <iomanip>
#include <math.h>
#include <cstdlib>
#include <cstring>
#include "Server.hxx"

void RobotFunctionality(int port)
{

    //====================================== PTHREADS ========================================
    // Set up thread affinities -- these can be used to run threads on specific cores
    // cpu_set_t cpuset0;
    // cpu_set_t cpuset1;
    // CPU_ZERO(&cpuset0);
    // CPU_ZERO(&cpuset1);
    // CPU_SET(0, &cpuset0);
    // CPU_SET(1, &cpuset1);

    // Set the main thread to use core 0
    // pthread_t current_thread = pthread_self();
    // pthread_setaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset0);

    // Create a thread for OpenIGT Communications
    // pthread_t _igtID;
    Server _igtModule = Server(18936);
    void *_joinIgt;
    _igtModule.ThreadIGT;
    // pthread_create(&_igtID, NULL, &Server::ThreadIGT, (void *)&_igtModule);
    // std::vector<Server *> _igtList = {&_igtModule};
    // pthread_setaffinity_np(_igtID, sizeof(cpu_set_t), &cpuset1);

    // Create and Launch the Server Thread
    // CustomWebServer *webServer = new CustomWebServer(_robot, _igtList, 30001);
    // pthread_t _serverThread;
    // void *_joinServer;
    // pthread_create(&_serverThread, NULL, &CustomWebServer::runServer, (void *)webServer);
    // pthread_setaffinity_np(_serverThread, sizeof(cpu_set_t), &cpuset1);

    //====================================== MAIN LOOP ========================================

    // Launch main robot program
    while (1)
    {
        // Sync the igtModule -- checks for differences between the current robot state and the
        // cached robot state and broadcasts only those changes via openIGTLink
        _igtModule.Sync();
    }

    // Wait for all threads to finish
    // pthread_join(_igtID, &_joinIgt);
    // pthread_join(_serverThread, &_joinServer);
}

int main(int argc, char *argv[])
{
    if (argc != 2) // check number of arguments
    {
        // If not correct, print usage
        std::cerr << "Usage: " << argv[0] << " <port>" << std::endl;
        std::cerr << "    <port>     : Port # (18944 in Slicer default)" << std::endl;
        exit(0);
    }
    int port = atoi(argv[1]);

    RobotFunctionality(port);

    return 0;
}
