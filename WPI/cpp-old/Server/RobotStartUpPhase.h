/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotStartUpPhase_h
#define __RobotStartUpPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotStartUpPhase : public RobotPhaseBase
{
public:
  RobotStartUpPhase(Robot *);
  ~RobotStartUpPhase();

  virtual const char *Name() { return "START_UP"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader *headerMsg);
  virtual void OnExit();

protected:
};

#endif //__RobotStartUpPhase_h
