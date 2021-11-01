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

#ifndef __RobotSimulatorTargetingPhase_h
#define __RobotSimulatorTargetingPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotSimulatorPhaseBase.h"

class RobotSimulatorTargetingPhase : public RobotSimulatorPhaseBase
{
public:

  RobotSimulatorTargetingPhase();
  ~RobotSimulatorTargetingPhase();

  virtual const char* Name() { return "TARGETING"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);

protected:
  
  // Has the simulator received a target matrix?
  int TargetFlag;

};

#endif //__RobotSimulatorTargetingPhase_h
