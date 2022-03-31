// NavigationSlicerScript.h
#ifndef _NAVIGATION_SLICER_SCRIPT
#define _NAVIGATION_SLICER_SCRIPT

// Prototype function declarations

void setSocketVars(char* hostname, int port);
void *startThread();
void *receivingFunction();

void SendStringToSlicer(char* argDeviceName,char* argMessage);
void SendStatusToSlicer(char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage);
void SendTransformToSlicer(char* argDeviceName, igtl::Matrix4x4& matrix, char *wpiDeviceName);

// void GetStringFromSlicer(const char* hostname, int port);
// void GetStatusFromSlicer(const char* hostname, int port);
// void GetTransformFromSlicer(const char* hostname, int port);

int ReceiveTransformFromSlicer(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
int ReceiveStatusFromSlicer(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);
int ReceiveStringFromSlicer(igtl::Socket * socket, igtl::MessageHeader::Pointer& header);

// Global Variables
struct Global{
   static char * hostname;
   static int port;
   static std::string globalDeviceName;
   // String variables 
   static std::string globalString;
   // Status variables
   static int globalArgCode;
   static int globalArgSubcode;
   static std::string globalArgErrorName;
   static std::string globalArgStatusStringMessage;
   // Transform variables
   static igtl::Matrix4x4 globalMatrix;
};

#endif







