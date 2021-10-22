//============================================================================
// Name        : SurgicalRobot.cpp
// Author      : Produced in the WPI AIM Lab
// Description : This file is where the code starts via the main function.
//				 It includes initializing the menu and setting up the system.
//============================================================================

#include <utility>
#include <memory>
#include "SurgicalRobot.hpp"
// #include ".\Test_Suite\Unit_Tests.h"
#include "./Test_Suite/Unit_Tests.h"

void RobotFunctionality(Robot *_robot, Robot *_cachedRobot, SPI _spi, FPGA_Utilities *_fpga_util, Timer _timer, unsigned int loopRate)
{

	Logger &log = Logger::GetInstance();

	//====================================== PTHREADS ========================================
	// Set up thread affinities -- these can be used to run threads on specific cores
	cpu_set_t cpuset0;
	cpu_set_t cpuset1;
	CPU_ZERO(&cpuset0);
	CPU_ZERO(&cpuset1);
	CPU_SET(0, &cpuset0);
	CPU_SET(1, &cpuset1);

	// Set the main thread to use core 0
	pthread_t current_thread = pthread_self();
	pthread_setaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset0);

	// Create a thread for OpenIGT Communications
	pthread_t _igtID;
	OpenIGTLink _igtModule = OpenIGTLink(_robot, _cachedRobot, 18936);
	void *_joinIgt;
	pthread_create(&_igtID, NULL, &OpenIGTLink::ThreadIGT, (void *)&_igtModule);
	vector<OpenIGTLink *> _igtList = {&_igtModule};
	pthread_setaffinity_np(_igtID, sizeof(cpu_set_t), &cpuset1);

	// Create and Launch the Server Thread
	CustomWebServer *webServer = new CustomWebServer(_robot, _igtList, 30001);
	pthread_t _serverThread;
	void *_joinServer;
	pthread_create(&_serverThread, NULL, &CustomWebServer::runServer, (void *)webServer);
	pthread_setaffinity_np(_serverThread, sizeof(cpu_set_t), &cpuset1);

	// Log that the communication threads have been launched
	log.Log("SPI, OpenIGT, and HttpServer Threads Launched...", LOG_LEVEL_INFO, true);

	//====================================== MAIN LOOP ========================================
	// Set encoder references to zero
	_robot->ZeroRobot();

	// Launch main robot program
	while (1)
	{
		//			_timer.tic();
		// This is the main robot functionality method -- specific to each system
		_robot->Update();

		//======================= LEDs ===============================
		// Check if the FootPedal Has been Pressed
		if (_fpga_util->IsFootPedalPressed())
		{
			// Set the E-Stop LED to Green if the Foot Pedal is pressed
			_fpga_util->SetControllerLEDState(1, 0, 1, 0);
		}
		else
		{
			// Set the E-Stop LED to Red if the Foot Pedal is not pressed
			_fpga_util->SetControllerLEDState(1, 1, 0, 0);
		}

		// Set the Network LED to Green
		_fpga_util->SetControllerLEDState(2, 0, 1, 0);

		// Check if any motor in the system has stalled
		if (_robot->CheckForStalls())
		{
			// Set the Controller LED to Purple if a Stall has been detected
			_fpga_util->SetControllerLEDState(3, 1, 0, 1);
		}
		else
		{
			// Set the Controller LED to Green if the system is okay
			_fpga_util->SetControllerLEDState(3, 0, 1, 0);
		}
		//===============================================================

		// Obtain data from Daughter Cards over SPI
		_spi.RunSPI();

		// Sync the igtModule -- checks for differences between the current robot state and the
		// cached robot state and broadcasts only those changes via openIGTLink
		_igtModule.Sync();

		// Profile code to mantain a consistent loop time
		do
		{
			_timer.toc();
		} while ((_timer.time()) < loopRate);
		//			log.Log("Time:" + to_string(_timer.time()), LOG_LEVEL_INFO, false);
	}

	// Wait for all threads to finish
	pthread_join(_igtID, &_joinIgt);
	pthread_join(_serverThread, &_joinServer);
}

int main(int argc, char *argv[])
{

	// Log that the system has been initialized
	Logger &log = Logger::GetInstance();
	log.Log("Starting robot system...", LOG_LEVEL_INFO, true);

	// Create a Packet Object that stores data exchanged over SPI
	// This object is a shared variable used in other parts of the program
	Packets _packets = Packets();

	// Create an FPGA Utility that handles NI functionalities
	FPGA_Utilities *_fpga_util = new FPGA_Utilities();
	_fpga_util->InitializeFPGA();
	sleep(2); // Wait two seconds while the fpga initializes

	// Create an SPI object to perform communication with Daughter Cards
	SPI _spi = SPI(&_packets, _fpga_util);

	// Create a Timer to profile the while loop at the bottom of this main() And determine a loop rate
	Timer _timer;
	unsigned int loopRate = 900; // microseconds

	//===================================== ROBOTS ==========================================
	// Launch Robot Objects -- Assume we're using the NeuroRobot unless told otherwise
	if (argc > 1 && strcmp(argv[1], "ProstateRobot") == 0)
	{
		log.Log("Launching Prostate Robot...", LOG_LEVEL_INFO, true);
		ProstateRobot _robot = ProstateRobot(&_packets, _fpga_util, loopRate);
		ProstateRobot _cachedRobot = ProstateRobot(&_packets, _fpga_util, loopRate);
		RobotFunctionality(&_robot, &_cachedRobot, _spi, _fpga_util, _timer, loopRate);
	}
	else
	{
		log.Log("Launching Neuro Robot...", LOG_LEVEL_INFO, true);
		NeuroRobot _robot = NeuroRobot(&_packets, _fpga_util, loopRate);
		NeuroRobot _cachedRobot = NeuroRobot(&_packets, _fpga_util, loopRate);
		RobotFunctionality(&_robot, &_cachedRobot, _spi, _fpga_util, _timer, loopRate);
	}

	return 0;
}
