/*=========================================================================

  Program:   BRP Prostate Robot: Testing Simulator (Robot)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#ifndef __RobotSimulatorUndefinedPhase_h
#define __RobotSimulatorUndefinedPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotSimulatorPhaseBase.h"

class RobotSimulatorUndefinedPhase : public RobotSimulatorPhaseBase
{
public:

  RobotSimulatorUndefinedPhase();
  ~RobotSimulatorUndefinedPhase();

  virtual const char* Name() { return "UNDEFINED"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);

protected:

};

#endif //__RobotSimulatorUndefinedPhase_h
