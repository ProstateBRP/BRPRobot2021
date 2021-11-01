/*=========================================================================

  Program:  BRP Prostate Robot: Testing Simulator (Robot)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#ifndef __TestBase_h
#define __TestBase_h

#include "igtlSocket.h"
#include "igtlMath.h"
#include "igtlMessageBase.h"

class TestBase
{
public:
  enum {
    ERROR = 0,
    SUCCESS = 1,
  };

public:
  TestBase();
  ~TestBase();

  virtual const char* Name()=0;

  void SetSocket(igtl::Socket* socket);
  int  ReceiveMessageHeader(igtl::MessageHeader* headerMsg, int timeout);
  int  SkipMesage(igtl::MessageHeader* headerMsg);
  void GetRandomTestMatrix(igtl::Matrix4x4& matrix);
  int  SendStringMessage(const char* name, const char* string);
  int  SendStatusMessage(const char* name, int Code, int SubCode,
                         const char * errorName=NULL, const char* statusString=NULL);
  int  SendTransformMessage(const char* name, igtl::Matrix4x4& matrix);

  /// Check if the received messsage is STRING message, and if the message has
  /// the specfied name and content. If suffix=1 is specified, the function
  /// only checks if the message name begins with the string specified by 'name'.
  /// For example, "CMD_1234" will be accepted when name="CMD_" and suffix=1 are
  /// specfiied. 
  int  CheckAndReceiveStringMessage(igtl::MessageHeader* headerMsg,
                                    const char* name, const char* string, int suffix=0);
  int  CheckAndReceiveStatusMessage(igtl::MessageHeader* headerMsg,
                                    const char* name, int code, int suffix=0,
                                    const char* errorName=NULL);
  int  CheckAndReceiveTransformMessage(igtl::MessageHeader* headerMsg,
                                       const char* name, igtl::Matrix4x4& matrix,
                                       double err = 1.0e-10, int suffix=0);

  int ReceiveTransform(igtl::MessageHeader* header, igtl::Matrix4x4& matrix);
  int ReceiveString(igtl::MessageHeader* header, std::string& string);
  int ReceiveStatus(igtl::MessageHeader* header, int& code, int& subcode,
                    std::string& name, std::string& status);

  void PrintMatrix(std::string prefix, igtl::Matrix4x4& matrix);
  int  ValidateMatrix(igtl::Matrix4x4& matrix);

  // Compare two matrices. If there is any corresponding elements with error larger than 'tol', return 0.
  // Otherwise, it returns 1.
  int  CompareMatrices(igtl::Matrix4x4& matrix1, igtl::Matrix4x4& matrix2, double tol);

protected:

  igtl::Socket::Pointer Socket;
};

#endif //__TestBase_h
