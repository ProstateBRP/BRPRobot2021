// LisaScript.h
#ifndef _LISA_SCRIPT
#define _LISA_SCRIPT

// prototype function declarations

// Following functions send different type message to Slicer
void SendStringToSlicer(char*  hostname, int port, char* argDeviceName,char* argMessage);
void SendStatusToSlicer(char*  hostname, int port, char* argDeviceName, unsigned short argCode, unsigned  long  long argSubcode, char* argErrorName, char* argStatusStringMessage);
void SendTransformToSlicer(const char* hostname, int port, char* argDeviceName, igtl::Matrix4x4& matrix);

// Following functions get different type message from Slicer
void GetStringFromSlicer(const char* hostname, int port);
void GetStateFromSlicer(const char* hostname, int port);
void GetTransformFromSlicer(const char* hostname, int port);

int getStatus();

#endif
