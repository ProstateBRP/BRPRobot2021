//============================================================================
// Name        : OpenIGTLink.hpp
// Author      : Produced in the WPI AIM Lab
// Description : This file is where OpenIGT requests are handled
//============================================================================

#ifndef OPENIGTLINK_HPP_
#define OPENIGTLINK_HPP_

// System includes
#include <iostream>
#include <iomanip>
#include <math.h>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

// Robot includes
#include "../Robot/Robot.hpp"
// IGTL includes
#include "igtlServerSocket.h"

// Work Phase includes
#include "RobotPhaseBase.h"
#include "RobotUndefinedPhase.h"
#include "RobotStartUpPhase.h"
#include "RobotPlanningPhase.h"
#include "RobotCalibrationPhase.h"
#include "RobotTargetingPhase.h"
#include "RobotMoveToTargetPhase.h"
#include "RobotManualPhase.h"
#include "RobotStopPhase.h"
#include "RobotEmergencyPhase.h"
#include "RobotStatus.h"

class OpenIGTLink
{
public:
	//================ Constructor ================
	OpenIGTLink(Robot *robot, int port);

	//================ Parameters =================
	 int clientSocketConnected{1};
	igtl::Socket::Pointer socket;
	Robot *robot;
	bool retransmit;
	int port;

	// For TCP Keep Alive
	bool keepAlive;
	Timer keepAliveTimer;
	std::vector<RobotPhaseBase* > WorkphaseList;

	//================ Public Methods ==============
	// This method receives data to the controller via OpenIGTLink
	static void *ThreadIGT(void *);
	int Session();
	// This method disconnect the current socket
	void DisconnectSocket();
};

#endif /* OPENIGTLINK_HPP_ */
