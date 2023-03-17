/*=========================================================================
  Language:  C++
  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the protocol.

=========================================================================*/

#include "RobotPhaseBase.h"
#include <string.h>
#include <stdlib.h>
#include "igtlOSUtil.h"
#include "igtlStringMessage.h"
#include "igtlClientSocket.h"
#include "igtlStatusMessage.h"
#include "igtlTransformMessage.h"
#include <cmath>

RobotPhaseBase::RobotPhaseBase()
{
  this->NextWorkphase.clear();
  this->RStatus = NULL;
}

RobotPhaseBase::~RobotPhaseBase()
{
}

int RobotPhaseBase::Enter(const char *queryID)
{
  // Send acknowledgement message with query ID
  std::stringstream ss;
  ss << "ACK_" << queryID;
  this->SendStringMessage(ss.str().c_str(), this->Name());
  Logger &log = Logger::GetInstance();
  log.Log("Changed Workphase to " + string(this->Name()), ss.str(), 1, 1);

  // Send phase message
  // TODO: Check if the phase transition is allowed
  this->SendStatusMessage("CURRENT_STATUS", 1, 0, this->Name());

  return this->Initialize();
}

int RobotPhaseBase::Process()
{
  // Create a message buffer to receive header
  igtl::MessageHeader::Pointer headerMsg;
  headerMsg = igtl::MessageHeader::New();

  ReceiveMessageHeader(headerMsg, 0);

  // If there is any workphase change request,
  // set NextWorkphase (done in the subroutine) and return 1.
  if (this->CheckWorkphaseChange(headerMsg))
  {
    return 1;
  }

  // Not when message is empty
  if (strcmp(headerMsg->GetDeviceName(), "") != 0)
  {
    // Otherwise, the current workphase is the next workphase.
    this->NextWorkphase = this->Name();                      // Set the name of the current workphase as the next one.
    std::cout << this->Name() << ": is the current state\n"; // Added it for test
  }

  // Common messages are handled here.
  if (!this->CheckCommonMessage(headerMsg))
  {
    MessageHandler(headerMsg);
  }

  return 0;
}

int RobotPhaseBase::MessageHandler(igtl::MessageHeader *headerMsg)
{
  return 0;
}

int RobotPhaseBase::CheckWorkphaseChange(igtl::MessageHeader *headerMsg)
{

  // Check if the message requests phase transition
  if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0 &&
      strncmp(headerMsg->GetDeviceName(), "CMD_", 4) == 0)
  {
    igtl::StringMessage::Pointer stringMsg;
    stringMsg = igtl::StringMessage::New();
    stringMsg->SetMessageHeader(headerMsg);
    stringMsg->AllocatePack();
    bool timeout(false);

    // The code waits here for new messages recieved from the socket
    int r = this->Socket->Receive(stringMsg->GetPackBodyPointer(), stringMsg->GetPackBodySize(), timeout);
    if (r < 0)
    {
      std::cerr << "ERROR: Timeout." << std::endl;
      this->Socket->CloseSocket();
      exit(EXIT_FAILURE);
    }
    else if (r == 0)
    {
      std::cerr << "ERROR: Socket closed while reading a message." << std::endl;
      this->Socket->CloseSocket();
      exit(EXIT_FAILURE);
    }

    // Deserialize the string message
    // If you want to skip CRC check, call Unpack() without argument.
    int c = stringMsg->Unpack(1);

    if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
    {
      if (stringMsg->GetEncoding() == 3)
      {
        this->NextWorkphase = stringMsg->GetString();
        std::cout << "Next Work Phase is: " << this->NextWorkphase << std::endl;
        // Get the query ID
        std::string msgName = headerMsg->GetDeviceName();
        this->QueryID = msgName.substr(4, std::string::npos);
        return 1;
      }
      else
      {
        this->NextWorkphase = "Unknown";
        return 1;
      }
    }
    else
    {
      std::cerr << "ERROR: Invalid CRC." << std::endl;
      this->NextWorkphase = "Unknown";
      return 1;
    }
  }
  else
  {
    return 0;
  }
}

// Checks for general communication messages that can be triggered from Slicer regardless of the current state.
int RobotPhaseBase::CheckCommonMessage(igtl::MessageHeader *headerMsg)
{
  // Check if the received message is string
  if (strcmp(headerMsg->GetDeviceType(), "STRING") == 0)
  {
    string dev_name;
    ReceiveString(headerMsg, dev_name);

    if (strcmp(dev_name.c_str(), "CURRENT_POSITION") == 0)
    {
      // Send current needle pose to Slicer
      igtl::Matrix4x4 curr_pose;
      RStatus->GetCurrentPosition(curr_pose);
      SendTransformMessage("CURRENT_POSITION", curr_pose);
      Logger &log = Logger::GetInstance();
      log.Log("Info: Sent CURRENT_POSITION to navigation", 1, 1);   
      // Send string msg flag for targeting position
      // TODO:
      // Send string msg flag for insertion depth
      // TODO:
      return 1;
    }
    else if (strcmp(dev_name.c_str(), "CURRENT_STATUS") == 0)
    {
      this->SendStatusMessage(this->Name(), 1, 0);
      Logger &log = Logger::GetInstance();
      log.Log("Info: Sent CURRENT_STATUS to navigation", 1, 1);
      return 1;
    }
  }

  
  else if (strcmp(headerMsg->GetDeviceType(), "STATUS") == 0)
  {
    bool timeout(false);
    int cc = headerMsg->Unpack(1);
    igtl::StatusMessage::Pointer statusMsg;
    statusMsg = igtl::StatusMessage::New();
    statusMsg->SetMessageHeader(headerMsg);
    statusMsg->AllocatePack();
    int r = this->Socket->Receive(statusMsg->GetPackBodyPointer(), statusMsg->GetPackBodySize(), timeout);
  }

  return 0;
}

void RobotPhaseBase::OnExit()
{
  // specific behaviour should be defined in child classes
}