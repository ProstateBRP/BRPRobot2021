/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#ifndef __RobotCalibrationPhase_h
#define __RobotCalibrationPhase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "RobotPhaseBase.h"

class RobotCalibrationPhase : public RobotPhaseBase
{
public:

  RobotCalibrationPhase(Robot*);
  ~RobotCalibrationPhase();

  virtual const char* Name() { return "CALIBRATION"; };

  virtual int Initialize();
  virtual int MessageHandler(igtl::MessageHeader* headerMsg);
  virtual void OnExit();

protected:

};

#endif //__RobotCalibrationPhase_h
