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
#include <iomanip>
#include <math.h>
#include <cstdlib>
#include <cstring>
#include "Client.hxx"

void ClientFunctionality(char* wpiHostname, int wpiPort, char* slicerHostname, int slicerPort)
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
    
    // Server _igtModule = Server(18936);
    // void *_joinIgt;
    // _igtModule.ThreadIGT;

    Client _igtModule = Client(wpiHostname, wpiPort, slicerHostname, slicerPort);
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

    // Launch main loop
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

    if (argc != 6) // check number of arguments
    {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>" << std::endl;
    std::cerr << "    <hostname> : IP or host name for WPI server connection" << std::endl;
    std::cerr << "    <port>     : Port # for WPI server connection" << std::endl;
    std::cerr << "    <slicerHostname> : IP or host name for Slicer server connection" << std::endl;
    std::cerr << "    <slicerPort>     : Port # for Slicer server connection" << std::endl;
    std::cerr << "    <fps>      : Frequency (fps) to send string" << std::endl;
    exit(0);
    }

    char *wpiHostname = argv[1];
    int wpiPort = atoi(argv[2]);
    char *slicerHostname = argv[3];
    int slicerPort = atoi(argv[4]);
    double fps = atof(argv[5]);
    int interval = (int)(1000.0 / fps);
    //char *deviceName = (char *)"deviceName";

    ClientFunctionality(wpiHostname, wpiPort, slicerHostname, slicerPort);

    return 0;
}