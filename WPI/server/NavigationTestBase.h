/*=========================================================================

  Program:   BRP Prostate Robot: Testing Simulator (Client)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#ifndef __NavigationTestBase_h
#define __NavigationTestBase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"
#include "TestBase.h"

#define DEFULT_TIMEOUT_SHORT  500
#define DEFULT_TIMEOUT_MEDIUM 1000
#define DEFULT_TIMEOUT_LONG   5000

class NavigationTestBase : public TestBase
{
public:

  // This type is used to return the check point in the test. The upper 16 bits
  // represents the step ID, while the lower 16 bits represents the point ID.
  // 0xFFFFFFFE and 0xFFFFFFFF are reserved for UNKOWN FAILURE and SUCCESS. 
  // Error() function may be used to generate ErrorPointType value.
  // To decode ErrorPointType values, use GetStep() and GetPoint().
  typedef unsigned int ErrorPointType;
  
  enum {
    UNKNOWN_FAILURE = 0xFFFFFFFE,
    SUCCESS = 0xFFFFFFFF,
  };

  int TimeoutShort;
  int TimeoutMedium;
  int TimeoutLong;

public:
  NavigationTestBase();
  ~NavigationTestBase();

  virtual const char* Name()=0;

  virtual int Exec();

  inline ErrorPointType Error(unsigned short step, unsigned short point)
  {
    ErrorPointType ret;
    ret = step;
    ret = (ret << 16) | point;
    return ret;
  }

  inline unsigned short GetStep(ErrorPointType error)
  {
    unsigned short ret;
    ret = error >> 16 & 0xFFFF;
    return ret;
  }

  inline unsigned short GetPoint(ErrorPointType error)
  {
    unsigned short ret;
    ret = error & 0xFFFF;
    return ret;
  }

  // Testing protocol implementation. This must be implemented in a child class.
  // Test() returns ErrorPoint data. 
  virtual ErrorPointType Test() = 0;


  // Set/Get timeout values. All timeout values are in millisecond
  inline void SetTimeoutShort(int ms)  { this->TimeoutShort  = ms; }
  inline void SetTimeoutMedium(int ms) { this->TimeoutMedium = ms; }
  inline void SetTimeoutLong(int ms)   { this->TimeoutLong   = ms; }

  inline int GetTimeoutShort()  { return this->TimeoutShort;  }
  inline int GetTimeoutMedium() { return this->TimeoutMedium; }
  inline int GetTimeoutLong()   { return this->TimeoutLong;   }

protected:

};

#endif //__NavigationTestBase_h
