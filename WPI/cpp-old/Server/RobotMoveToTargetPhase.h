/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotMoveToTargetPhase_h
#define __RobotMoveToTargetPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotMoveToTargetPhase : public RobotPhaseBase
{
public:
  RobotMoveToTargetPhase(Robot *);
  ~RobotMoveToTargetPhase();

  virtual const char *Name() { return "MOVE_TO_TARGET"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader *headerMsg);
  virtual void OnExit();

};

#endif //__RobotMoveToTargetPhase_h
