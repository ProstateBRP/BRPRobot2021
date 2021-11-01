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

#ifndef __RobotSimulatorMoveToTargetPhase_h
#define __RobotSimulatorMoveToTargetPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotSimulatorPhaseBase.h"

class RobotSimulatorMoveToTargetPhase : public RobotSimulatorPhaseBase
{
public:

  RobotSimulatorMoveToTargetPhase();
  ~RobotSimulatorMoveToTargetPhase();

  virtual const char* Name() { return "MOVE_TO_TARGET"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);

protected:
  
  // Has the simulator received a target matrix?
  int TargetFlag;

};

#endif //__RobotSimulatorMoveToTargetPhase_h
