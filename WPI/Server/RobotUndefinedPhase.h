/*=========================================================================

  Program:   BRP Prostate Robot: Testing  (Robot)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#ifndef __RobotUndefinedPhase_h
#define __RobotUndefinedPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotUndefinedPhase : public RobotPhaseBase
{
public:

  RobotUndefinedPhase();
  ~RobotUndefinedPhase();

  virtual const char* Name() { return "UNDEFINED"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);
  virtual void OnExit();

protected:

};

#endif //__RobotUndefinedPhase_h
