//============================================================================
// Name        : OpenIGTLink.hpp
// Author      : Produced in the WPI AIM Lab
// Description : This file is where OpenIGT requests are handled
//============================================================================

#ifndef OPENIGTLINK_HPP_
#define OPENIGTLINK_HPP_

using namespace std;
#include <string.h>

 #include "..\..\Robots\Robot.hpp"
 #include "..\..\Robots\NeuroRobot\NeuroRobot.hpp"
 #include "..\..\Robots\ProstateRobot\ProstateRobot.hpp"
//#include "../../Robots/Robot.hpp"
//#include "../../Robots/NeuroRobot/NeuroRobot.hpp"
//#include "../../Robots/ProstateRobot/ProstateRobot.hpp"

#include "igtlTransformMessage.h"
#include "igtlOSUtil.h"
#include "igtlMessageHeader.h"
#include "igtlTransformMessage.h"
#include "igtlStringMessage.h"
#include "igtlImageMessage.h"
#include "igtlServerSocket.h"
#include "igtlStatusMessage.h"
#include "igtlPositionMessage.h"
#include "igtlPointMessage.h"
#include "igtlClientSocket.h"
#include "igtlNDArrayMessage.h"

class OpenIGTLink
{
public:
	//================ Constructor ================
	OpenIGTLink(Robot *robot, Robot *_cachedRobot, int port);

	//================ Parameters =================
	int _clientSocketConnected;
	igtl::Socket::Pointer socket;
	Robot *_cachedRobot;
	Robot *_robot;
	bool _retransmit;
	int _port;

	// For TCP Keep Alive
	bool _keepAlive;
	Timer _keepAliveTimer;

	//================ Public Methods ==============
	// This method receives data to the controller via OpenIGTLink
	static void *ThreadIGT(void *);

	// This method sends data out from the controller via OpenIGTLink, given some change in robot state
	void Sync();

	// This method disconnect the current socket
	void DisconnectSocket();

	// Methods got Receiving various IGT Data Types
	int ReceiveStatus(igtl::Socket *socket, igtl::MessageHeader *header);
	string ReceiveString(igtl::Socket *socket, igtl::MessageHeader *header);
	Eigen::Matrix4d ReceiveTransform(igtl::Socket *socket, igtl::MessageHeader *header);
	vector<int> ReceiveArray(igtl::Socket *socket, igtl::MessageHeader *header);
};

#endif /* OPENIGTLINK_HPP_ */
