// LisaScript.h
#ifndef _LISA_SCRIPT
#define _LISA_SCRIPT

// prototype function declarations
void SendStringToSlicer(char*  hostname, int port, char* argDeviceName,char* argMessage);
void startup();
int getTransform();
int getStatus();


#endif

