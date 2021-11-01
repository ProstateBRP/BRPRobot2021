// LisaScript.h
#ifndef _LISA_SCRIPT
#define _LISA_SCRIPT

// Prototype function declarations

void SendStringToSlicer(char*  hostname, int port, char* argDeviceName,char* argMessage);
void SendStateToSlicer(char*  hostname, int port, char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage);
void SendTransformToSlicer(const char* hostname, int port, char* argDeviceName, igtl::Matrix4x4& matrix);


int getTransform();
int getStatus();


void GetStringFromSlicer(const char* hostname, int port);
void GetStateFromSlicer(const char* hostname, int port);
void GetTransformFromSlicer(const char* hostname, int port);

int ReceiveTransform(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
int ReceiveStatus(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
int ReceiveString(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);

// Global Variables


struct Global{
   static std::string myglobalstring;
   static std::string past_globalstring;
};

#endif







