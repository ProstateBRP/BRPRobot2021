/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotPhaseBase_h
#define __RobotPhaseBase_h

#include <string>
#include <map>

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotCommunicationBase.h"
#include "RobotStatus.h"
#include "../Utilities/Logger/Logger.hpp"
class RobotPhaseBase : public RobotCommunicationBase
{
public:
  RobotPhaseBase();
  virtual ~RobotPhaseBase(); // Changed the destructor to virtual

  virtual const char *Name() = 0;

  // Enter() will be called when the workphase is switched from another
  // workphase. Enter() calls Initialize() which implements actual
  // initialization process for this workphase.
  virtual int Enter(const char *queryID);

  // Initialization process. This must be implemented in child classes.
  virtual int Initialize() = 0;

  // Process() will be called by the main session loop.
  // It checks if any work phase change request is received first. If not it calls
  // MessageHander() to perform workphase-specific message handling.
  // Returns 1 if there is any workphase change request. Otherwise returns 0.
  virtual int Process();

  // MessageHandler() defines workphase-specific message handling.
  // The function needs to be implemented in child classes.
  virtual int MessageHandler(igtl::MessageHeader *headerMsg); // Message handler

  std::string GetNextWorkPhase() { return this->NextWorkphase; };
  std::string GetQueryID() { return this->QueryID; };
  
  void SetRobotStatus(RobotStatus *rs) { this->RStatus = rs; };
  // Get robot status
  RobotStatus* GetRobotStatus(){return this->RStatus;};

protected:
  // Check if a CMD message (workphase change) has been received.
  // Return 1, if workphase change has been requested.
  int CheckWorkphaseChange(igtl::MessageHeader *headerMsg);

  // Check if there is any messages that must be accepted
  // regardless of current workhpase.
  int CheckCommonMessage(igtl::MessageHeader *headerMsg);

  // Register defect type.
  // int RegisterDefectType(const char *name, const char *desc);

  std::string NextWorkphase;
  std::string QueryID;

  // std::map<std::string, int> DefectStatus;
  // std::map<std::string, std::string> DefectDescription;

  RobotStatus *RStatus;
};

#endif //__RobotPhaseBase_h
