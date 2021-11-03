// LisaScript.h
#ifndef _LISA_SCRIPT
#define _LISA_SCRIPT

// Prototype function declarations

void setSocketVars(char* hostname, int port);

void SendStringToSlicer(char* argDeviceName,char* argMessage);
void SendStateToSlicer(char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage);
void SendTransformToSlicer(char* argDeviceName, igtl::Matrix4x4& matrix);


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
   static char * hostname;
   static int port;
   static std::string myglobalstring;
   static std::string past_globalstring;
};

#endif







