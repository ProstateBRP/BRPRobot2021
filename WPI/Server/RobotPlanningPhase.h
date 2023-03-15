/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotPlanningPhase_h
#define __RobotPlanningPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotPlanningPhase : public RobotPhaseBase
{
public:

  RobotPlanningPhase();
  ~RobotPlanningPhase();

  virtual const char* Name() { return "PLANNING"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);

protected:

};

#endif //__RobotPlanningPhase_h
