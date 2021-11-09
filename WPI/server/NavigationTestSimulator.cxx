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
#include "NavigationNormalOperationTest.h"
#include "NavigationStartUpErrorTest.h"
#include "NavigationCalibrationErrorTest.h"
#include "NavigationTargetingWithoutCalibrationTest.h"
#include "NavigationOutOfRangeTest.h"
#include "NavigationStopDuringOperationTest.h"
#include "NavigationEmergencyStopDuringOperationTest.h"
#include "NavigationMoveToWithoutTargetTest.h"
#include "NavigationAccidentalCommandDuringManualModeTest.h"
#include "NavigationHardwareErrorDuringOperationTest.h"

int main(int argc, char* argv[])
{
  //------------------------------------------------------------
  // Parse Arguments

  if (argc != 4) // check number of arguments
    {
    // If not correct, print usage
    std::cerr << "Usage: " << argv[0] << " <hostname> <port> <string>"    << std::endl;
    std::cerr << "    <hostname> : IP or host name"                    << std::endl;
    std::cerr << "    <port>     : Port # (18944 in Slicer default)"   << std::endl;
    std::cerr << "    <test>     : Test # (1-10)"   << std::endl;
    exit(0);
    }

  char*  hostname = argv[1];
  int    port     = atoi(argv[2]);
  int    test     = atoi(argv[3]);

  if (test <= 0 || test > 10)
    {
    std::cerr << "Invalid test" << std::endl;
    exit(0);
    }

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
  // Call Test
  NavigationTestBase* navTest = NULL;

  switch (test)
    {
    case 1:
      {
      navTest = (NavigationNormalOperationTest*) new NavigationNormalOperationTest();
      break;
      }
    case 2:
      {
      navTest = (NavigationStartUpErrorTest*) new NavigationStartUpErrorTest();
      break;
      }
    case 3:
      {
      navTest = (NavigationCalibrationErrorTest*) new NavigationCalibrationErrorTest();
      break;
      }
    case 4:
      {
      navTest = (NavigationTargetingWithoutCalibrationTest*) new NavigationTargetingWithoutCalibrationTest();
      break;
      }
    case 5:
      {
      navTest = (NavigationOutOfRangeTest*) new NavigationOutOfRangeTest();
      break;
      }
    case 6:
      {
      navTest = (NavigationStopDuringOperationTest*) new NavigationStopDuringOperationTest();
      break;
      }
    case 7:
      {
      navTest = (NavigationEmergencyStopDuringOperationTest*) new NavigationEmergencyStopDuringOperationTest();
      break;
      }
    case 8:
      {
      navTest = (NavigationMoveToWithoutTargetTest*) new NavigationMoveToWithoutTargetTest();
      break;
      }
    case 9:
      {
      navTest = (NavigationAccidentalCommandDuringManualModeTest*) new NavigationAccidentalCommandDuringManualModeTest();
      break;
      }
    case 10:
      {
      navTest = (NavigationHardwareErrorDuringOperationTest*) new NavigationHardwareErrorDuringOperationTest();
      break;
      }
    default:
      break;
    }

  if (navTest)
    {
    // Set timeout values (ms)
    navTest->SetTimeoutShort(1000);
    navTest->SetTimeoutMedium(5000);
    navTest->SetTimeoutMedium(10000);

    navTest->SetSocket(socket);
    navTest->Exec();
    }

  //------------------------------------------------------------
  // Close connection

  socket->CloseSocket();
}

