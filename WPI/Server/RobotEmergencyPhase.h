/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotEmergencyPhase_h
#define __RobotEmergencyPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotEmergencyPhase : public RobotPhaseBase
{
public:
  RobotEmergencyPhase(Robot *);
  ~RobotEmergencyPhase();

  virtual const char *Name() { return "EMERGENCY"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader *headerMsg);
  virtual void OnExit();

protected:
};

#endif //__RobotEmergencyPhase_h
