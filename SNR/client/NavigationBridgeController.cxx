/*=========================================================================

  Program:   BRP Prostate Robot: Testing Simulator (Client)
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
#include <math.h>
#include <cstdlib>

#include "igtlClientSocket.h"
#include "NavigationBridge.h"
#include "NavigationSlicerScript.hxx"

#include "thread"

int main(int argc, char* argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

  if (argc != 5) // check number of arguments
  {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>"    << std::endl;
    std::cerr << "    <wpiHostname> : IP or hostname for WPI robot server connection" << std::endl;
    std::cerr << "    <wpiPort>     : Port # for WPI robot server connection"   << std::endl;
    std::cerr << "    <snrHostname> : IP or hostname for Slicer server connection" << std::endl;
    std::cerr << "    <snrPort>     : Port # for Slicer server connection" << std::endl;
    exit(0);
  }

  char*  wpiHostname = argv[1];
  int    wpiPort     = atoi(argv[2]);
  char*  snrHostname = argv[3];
  int    snrPort     = atoi(argv[4]);

  //------------------------------------------------------------
  // Establish Connection

  igtl::ClientSocket::Pointer socket;
  socket = igtl::ClientSocket::New();
  int r = socket->ConnectToServer(wpiHostname, wpiPort);

  if (r != 0)
  {
    std::cerr << "Cannot connect to the server." << std::endl;
    exit(0);
  }

  // Call function in NavigationSlicerScript.cxx to establish connection and start the thread that receives messages from Slicer
  setSocketVars(snrHostname, snrPort);

  // Call startThread function in NavigationSlicerScript.cxx in a thread s.t. the rest of main() continues to run simultaneously
  std::thread thr(&startThread);
  thr.detach();

  //------------------------------------------------------------
  // Call Test
  NavigationIGTControlBase* navTest = NULL;
  
  std::cout << "------------------- Starting NavigationBridge -------------------" << std::endl;
  navTest = (NavigationBridge*) new NavigationBridge();

  if (navTest)
  {
    // Set timeout values (ms)
    navTest->SetTimeoutShort(1000);
    navTest->SetTimeoutMedium(5000);
    navTest->SetTimeoutLong(10000);

    navTest->SetSocket(socket);
    navTest->Exec();
  }

  //------------------------------------------------------------
  // Close connection

  socket->CloseSocket();
}

