// LisaScript.h
#ifndef _LISA_SCRIPT
#define _LISA_SCRIPT

// prototype function declarations
//int ReceiveString(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
void SendStringToSlicer(char*  hostname, int port, char*  argDeviceName,char*  argMessage);


#endif

