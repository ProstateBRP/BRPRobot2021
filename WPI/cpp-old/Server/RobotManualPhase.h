/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotManualPhase_h
#define __RobotManualPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotManualPhase : public RobotPhaseBase
{
public:

  RobotManualPhase(Robot *);
  ~RobotManualPhase();

  virtual const char* Name() { return "MANUAL"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);
  virtual void OnExit();

protected:

};

#endif //__RobotManualPhase_h
