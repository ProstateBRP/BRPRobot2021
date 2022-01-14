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

#include "NavigationIGTControlBase.h"
#include <string.h>
#include <stdlib.h>

#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

#include "NavigationSlicerScript.hxx"

NavigationIGTControlBase::NavigationIGTControlBase()
{
  this->TimeoutShort  = DEFULT_TIMEOUT_SHORT;
  this->TimeoutMedium = DEFULT_TIMEOUT_MEDIUM;
  this->TimeoutLong   = DEFULT_TIMEOUT_LONG;
  this->TimeoutFalse  = DEFAULT_TIMEOUT_FALSE;
}


NavigationIGTControlBase::~NavigationIGTControlBase()
{
}


int NavigationIGTControlBase::Exec()
{
  if (this->Socket.IsNotNull())
    {
    ErrorPointType errorPoint = this->Test();
    if (errorPoint == SUCCESS)
      {
      std::cerr << "MESSAGE: The test has been completed successfully." << std::endl;
      Global::testRunning = false;
      return 1;
      }
    else
      {
      std::cerr << "ERROR: Test failed at check point #" << GetStep(errorPoint) << "." << GetPoint(errorPoint) << std::endl;
      Global::testRunning = false;
      return 0;
      }
    }
  else
    {
    std::cerr << "ERROR: Socket is not available."  << std::endl;
    Global::testRunning = false;
    return 0;
    }
}