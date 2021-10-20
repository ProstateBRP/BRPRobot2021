// LisaScript.h
#ifndef _LISA_SCRIPT
#define _LISA_SCRIPT

// prototype function declarations
void SendStringToSlicer(char*  hostname, int port, char* argDeviceName,char* argMessage);
void SendStatusToSlicer(char*  hostname, int port, char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage);
void SendTransformToSlicer(const char* hostname, int port, char* argDeviceName, igtl::Matrix4x4& matrix);

int getTransform();
int getStatus();


#endif
