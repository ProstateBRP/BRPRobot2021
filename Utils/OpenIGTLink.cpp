//============================================================================
// Name        : OpenIGTLink.hcpp
// Author      : Produced in the WPI AIM Lab
// Description : This file is where OpenIGT requests are handled
//============================================================================

// TODO: Make NDArray and Point Types For Transferring Data over OpenIGTLink

#include "OpenIGTLink.hpp"

OpenIGTLink::OpenIGTLink(Robot *robot, Robot *cachedRobot, int port)
{
	_clientSocketConnected = 0;
	socket = igtl::ClientSocket::New();
	_robot = robot;
	_port = port;

	// Create a cached robot to save robot state
	// Only transmit to external collection if there has been a change in robot state
	_cachedRobot = cachedRobot;

	// On new connections retransmit robot state
	_retransmit = false;

	// Does the client have a keep alive functionality?
	_keepAlive = false;
}

void *OpenIGTLink::ThreadIGT(void *igt)
{
	// For Profiling the code
	Timer _timer;
	Logger &log = Logger::GetInstance();

	// Get an IGT Object
	OpenIGTLink *igtModule = (OpenIGTLink *)igt;

	// Create New Sockets on the provided port
	igtl::ServerSocket::Pointer serverSocket;
	serverSocket = igtl::ServerSocket::New();
	int r = serverSocket->CreateServer(igtModule->_port);

	// Check if we can create a server socket
	if (r < 0)
	{
		// If we cannot error back
		std::cerr << "Cannot create a server socket." << std::endl;
		exit(1);
	}

	// While we are listening on this port
	while (1)
	{

		// Check if we can connect on the client socket
		igtModule->socket = serverSocket->WaitForConnection(1000);

		// Connection Specific Variables State -- Not Connected
		igtModule->_robot->_socketIGTConnection = "Listening";
		igtModule->_clientSocketConnected = 0;

		// If we were able to connect to the client socket
		if (igtModule->socket.IsNotNull())
		{
			// Connection Specific Variables State -- Connected
			igtModule->_robot->_socketIGTConnection = "Connected";
			igtModule->_clientSocketConnected = -1;

			// Create a message buffer to receive header
			igtl::MessageHeader::Pointer headerMsg;
			headerMsg = igtl::MessageHeader::New();

			// Allocate a time stamp
			igtl::TimeStamp::Pointer ts;
			ts = igtl::TimeStamp::New();

			// Initial keep alive timer tic
			if (igtModule->_keepAlive)
			{
				igtModule->_keepAliveTimer.tic();
			}

			// While the socket is not null and we're connected to the the client socket
			while (igtModule->socket.IsNotNull() && igtModule->_clientSocketConnected != 0)
			{

				// Initialize receive buffer
				// Receive generic header from the socket
				headerMsg->InitPack();

				// To preserve asynchonicity set a time out for how long to wait to receive data
				igtModule->socket->SetReceiveTimeout(1000); // In milliseconds

				// -- The _clientSocketConnected variable becomes zero when the Receive method is no longer connected to the client
				igtModule->_clientSocketConnected = igtModule->socket->Receive(headerMsg->GetPackPointer(), headerMsg->GetPackSize());

				// Check that the received data is valid, else just listen again
				if (igtModule->_clientSocketConnected > 0)
				{

					// De-serialize the header
					headerMsg->Unpack();

					// For profiling OpenIGTLink Communication
					_timer.tic();

					// Get time stamp
					igtlUint32 sec;
					igtlUint32 nanosec;
					headerMsg->GetTimeStamp(ts);
					ts->GetTimeStamp(&sec, &nanosec);

					//==========================================================================================
					//==========================================================================================
					// OPENIGTLINK MRI ROBOT RX PROTOCOLS

					//  REQUEST: NAME -- CURRENT_POSE & TYPE -- TRANSFORM
					if ((strcmp(headerMsg->GetDeviceName(), "CURRENT_POSE") == 0) && (strcmp(headerMsg
																								 ->GetDeviceType(),
																							 "TRANSFORM") == 0))
					{
						igtModule->_robot->_currentPose = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
						log.Log("OpenIGTLink Current Pose Received and Set in Code", LOG_LEVEL_INFO, true);
					}

					// REQUEST: NAME -- REGISTRATION & TYPE -- TRANSFORM
					else if ((strcmp(headerMsg->GetDeviceName(), "REGISTRATION") == 0) && (strcmp(headerMsg
																									  ->GetDeviceType(),
																								  "TRANSFORM") == 0))
					{
						igtModule->_robot->_registration = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
						log.Log("OpenIGTLink Registration Received and Set in Code", LOG_LEVEL_INFO, true);
					}

					// REQUEST: NAME -- TIP POSE & TYPE -- TRANSFORM wrt to imager plane
					else if ((strcmp(headerMsg->GetDeviceName(), "TIP_POSE") == 0) && (strcmp(headerMsg
																								  ->GetDeviceType(),
																							  "TRANSFORM") == 0))
					{
						igtModule->_robot->_imagerTip = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
						igtModule->_robot->RunInverseKinematics(0);
						log.Log("OpenIGTLink Tip Pose Received and Set in Code", LOG_LEVEL_INFO, true);
					}

					// REQUEST: TYPE -- STRING
					else if ((strcmp(headerMsg->GetDeviceName(), "TARGET_STATUS") == 0) && (strcmp(headerMsg
																									   ->GetDeviceType(),
																								   "STRING") == 0))
					{
						igtModule->_robot->_imagerStatus = igtModule->ReceiveString(igtModule->socket, headerMsg);
						log.Log("Target Status: " + igtModule->_robot->_imagerStatus, LOG_LEVEL_INFO, true);
					}

					// REQUEST: TYPE -- STATUS
					else if (strcmp(headerMsg->GetDeviceName(), "GET_STATUS") == 0)
					{
						// Send status messages
						igtl::StatusMessage::Pointer statusMsg = igtl::StatusMessage::New();
						statusMsg->SetDeviceName("STATUS");
						statusMsg->SetCode(1);
						statusMsg->Pack();
						igtModule->socket->Send(statusMsg->GetPackPointer(), statusMsg->GetPackSize());

						// If we are keeping track of the client keep alive messages
						if (igtModule->_keepAlive)
						{
							igtModule->_keepAliveTimer.tic();
						}
					}

					// REQUEST: NAME -- ABLATION_ANGLE & REQUEST: TYPE -- STRING
					else if ((strcmp(headerMsg->GetDeviceName(), "ABLATION_ANGLE") == 0) && (strcmp(headerMsg
																										->GetDeviceType(),
																									"STRING") == 0))
					{
						// Specific to NeuroRobot
						// Receive angle in radians from MATLAB Lesion Map Simulation Code
						string angle = igtModule->ReceiveString(igtModule->socket, headerMsg);

						Motor *_motor = igtModule->_robot->GetMotor(1);				  // Only for NeuroRobot
						_motor->_setpoint = int(stod(angle) * _motor->_ticksPerUnit); // convert to ticks
																					  // log.Log("Ablation Angle: " + angle, LOG_LEVEL_INFO, true);
					}

					// REQUEST: NAME -- ENTRY_POINT & REQUEST: TYPE -- TRANSFORM
					else if ((strcmp(headerMsg->GetDeviceName(), "ENTRY_POINT") == 0) && (strcmp(headerMsg
																									 ->GetDeviceType(),
																								 "TRANSFORM") == 0))
					{
						//
						Eigen::Matrix4d entryPointScannerCoordinates = igtModule->ReceiveTransform(igtModule->socket, headerMsg);

						igtModule->_robot->_entryPoint(0) = (double)entryPointScannerCoordinates(0, 3);
						igtModule->_robot->_entryPoint(1) = (double)entryPointScannerCoordinates(1, 3);
						igtModule->_robot->_entryPoint(2) = (double)entryPointScannerCoordinates(2, 3);

						// Recalculate InverseKinematics and Setpoints
						igtModule->_robot->RunInverseKinematics(1);
						log.Log("OpenIGTLink Entry Point Received and Set in Code", LOG_LEVEL_INFO, true);
					}

					// REQUEST: NAME -- TARGET_POINT & REQUEST: TYPE -- TRANSFORM
					else if ((strcmp(headerMsg->GetDeviceName(), "TARGET_POINT") == 0) && (strcmp(headerMsg
																									  ->GetDeviceType(),
																								  "TRANSFORM") == 0))
					{
						//
						// Eigen::Matrix4d targetPoseRobot = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
						// Eigen::Matrix4d targetPointScannerCoordinates = targetPoseRobot;
						Eigen::Matrix4d targetPointScannerCoordinates = igtModule->ReceiveTransform(igtModule->socket,
																									headerMsg);

						igtModule->_robot->_targetPoint(0) = (double)targetPointScannerCoordinates(0, 3);
						igtModule->_robot->_targetPoint(1) = (double)targetPointScannerCoordinates(1, 3);
						igtModule->_robot->_targetPoint(2) = (double)targetPointScannerCoordinates(2, 3);
						// Giving full target pose to the robot as well. Is used for the NeuroRobot
						igtModule->_robot->_targetPointFullPoseScanner = targetPointScannerCoordinates;

						// Recalculate InverseKinematics and Setpoints
						igtModule->_robot->RunInverseKinematics(1);
						log.Log("OpenIGTLink Target Point Received and Set in Code", LOG_LEVEL_INFO, true);
					}

					//==========================================================================================
					//==========================================================================================
					// CRTK Functions

					// *** SERVO_CP ***
					else if ((strcmp(headerMsg->GetDeviceName(), "servo_cp") == 0) && (strcmp(headerMsg->GetDeviceType(), "TRANSFORM") == 0))
					{
						//
						Eigen::Matrix4d targetPoseRobot = igtModule->ReceiveTransform(igtModule->socket, headerMsg);
						Eigen::Matrix4d targetPointScannerCoordinates = igtModule->_robot->_registration * targetPoseRobot;

						igtModule->_robot->_targetPoint(0) = (double)targetPointScannerCoordinates(0, 3);
						igtModule->_robot->_targetPoint(1) = (double)targetPointScannerCoordinates(1, 3);
						igtModule->_robot->_targetPoint(2) = (double)targetPointScannerCoordinates(2, 3);

						// Recalculate InverseKinematics and Setpoints
						igtModule->_robot->RunInverseKinematics(1);
						log.Log("OpenIGTLink CRTK Servo CP", LOG_LEVEL_INFO, true);
					}

					// *** SERVO JP ***
					else if ((strcmp(headerMsg->GetDeviceName(), "servo_jp") == 0) && (strcmp(headerMsg->GetDeviceType(), "ARRAY") == 0))
					{
						// Move joints individually -- bang bang control
						vector<int> joints = igtModule->ReceiveArray(igtModule->socket, headerMsg);
						vector<Motor *> motors = igtModule->_robot->ListMotors();

						if (joints.size() == motors.size())
						{
							for (uint i = 0; i < motors.size(); i++)
							{
								// Set to desired joints
								motors[i]->_setpoint = joints[i];
							}

							// Check if setpoints are valid
							igtModule->_robot->Axis_Setpoint_Validator();
						}

						log.Log("OpenIGTLink CRTK Servo JP", LOG_LEVEL_INFO, true);
					}

					//==========================================================================================
					//==========================================================================================

					// REQUEST: TYPE -- UNKNOWN
					else
					{
						igtModule->socket->Skip(headerMsg->GetBodySizeToRead(), 0);
						log.Log("OpenIGTLink Unknown Message Type", LOG_LEVEL_INFO, true);
					}

					do
					{
						_timer.toc();
					} while ((_timer.time()) < 500);

					// End profile Code
					// log.Log("Time IGT:" + to_string(_timer.time()), LOG_LEVEL_INFO, true);
				}

				// If we are keeping track of the client keep alive messages
				if (igtModule->_keepAlive)
				{
					// If the timer has not been tic'd in five seconds
					igtModule->_keepAliveTimer.toc();
					if (igtModule->_keepAliveTimer.time() > 5000000)
					{
						// Presume the client killed and disconnect the client socket
						log.Log("Client has not sent a keep alive in some time -- presuming killed -- disconnecting socket", LOG_LEVEL_INFO, true);
						igtModule->DisconnectSocket();
					}
				}
			}
		}

		// On new connections re-transmit robot states
		igtModule->_retransmit = true;
	}

	// On thread end, close the socket
	igtModule->DisconnectSocket();
	return NULL;
}

void OpenIGTLink::Sync()
{
	// Given that the socket is not null and we're connected to a client socket
	if (socket.IsNotNull() && _clientSocketConnected != 0)
	{

		// SEND ROBOT CURRENT POSE
		if (!_robot->_currentPose.isApprox(_cachedRobot->_currentPose) || _retransmit)
		{
			// Convert Eigen Matrix to IGT Matrix and update the cached robot
			igtl::Matrix4x4 msg;

			for (int i = 0; i < 4; i++)
			{
				for (int j = 0; j < 4; j++)
				{
					msg[i][j] = _robot->_currentPose(i, j);
				}
			}

			_cachedRobot->_currentPose = _robot->_currentPose;

			// Create Transformation Matrix to transmit
			igtl::TransformMessage::Pointer currentPoseMsg = igtl::TransformMessage::New();
			// currentPoseMsg->SetDeviceName("scanner_to_robot_cur"); // measured_cp
			currentPoseMsg->SetDeviceName("measured_cp");
			currentPoseMsg->SetMatrix(msg);
			currentPoseMsg->Pack();
			socket->Send(currentPoseMsg->GetPackPointer(), currentPoseMsg->GetPackSize());
		}

		// SEND ROBOT TARGET POSE
		if (!_robot->_targetPose.isApprox(_cachedRobot->_targetPose) || _retransmit)
		{
			// Convert Eigen Matrix to IGT Matrix and update the cached robot
			igtl::Matrix4x4 msg;

			for (int i = 0; i < 4; i++)
			{
				for (int j = 0; j < 4; j++)
				{
					msg[i][j] = _robot->_targetPose(i, j);
				}
			}

			_cachedRobot->_targetPose = _robot->_targetPose;

			// Create Transformation Matrix to transmit
			igtl::TransformMessage::Pointer targetPoseMsg = igtl::TransformMessage::New();
			// currentPoseMsg->SetDeviceName("scanner_to_robot_cur"); // measured_cp
			targetPoseMsg->SetDeviceName("desired_cp");
			targetPoseMsg->SetMatrix(msg);
			targetPoseMsg->Pack();
			socket->Send(targetPoseMsg->GetPackPointer(), targetPoseMsg->GetPackSize());
		}

		// SEND ROBOT REGISTRATION
		if (!_robot->_registration.isApprox(_cachedRobot->_registration) || _retransmit)
		{
			// Convert Eigen Matrix to IGT Matrix and update the cached robot
			igtl::Matrix4x4 msg;

			for (int i = 0; i < 4; i++)
			{
				for (int j = 0; j < 4; j++)
				{
					msg[i][j] = _robot->_registration(i, j);
				}
			}

			_cachedRobot->_registration = _robot->_registration;

			// Create Transformation Matrix to transmit
			igtl::TransformMessage::Pointer registrationMsg = igtl::TransformMessage::New();
			registrationMsg->SetDeviceName("scanner_to_robot_reg");
			registrationMsg->SetMatrix(msg);
			registrationMsg->Pack();
			socket->Send(registrationMsg->GetPackPointer(), registrationMsg->GetPackSize());
		}

		// SEND ROBOT ENTRY POINT
		if (!_robot->_entryPoint.isApprox(_cachedRobot->_entryPoint) || _retransmit)
		{
			// Convert Eigen Vector to IGT Point and update the cached robot
			igtl::PointElement::Pointer entryPoint = igtl::PointElement::New();
			entryPoint->SetPosition(_robot->_entryPoint(0), _robot->_entryPoint(1), _robot->_entryPoint(2));

			_cachedRobot->_entryPoint = _robot->_entryPoint;

			// Create Transformation Matrix to transmit
			igtl::PointMessage::Pointer entryMsg = igtl::PointMessage::New();
			entryMsg->SetDeviceName("entry_point");
			entryPoint->SetName("entry_point");
			entryMsg->AddPointElement(entryPoint);
			entryMsg->Pack();
			socket->Send(entryMsg->GetPackPointer(), entryMsg->GetPackSize());
		}

		// SEND ROBOT TARGET POINT
		if (!_robot->_targetPoint.isApprox(_cachedRobot->_targetPoint) || _retransmit)
		{
			// Convert Eigen Vector to IGT Point and update the cached robot
			igtl::PointElement::Pointer targetPoint = igtl::PointElement::New();
			targetPoint->SetPosition(_robot->_targetPoint(0), _robot->_targetPoint(1), _robot->_targetPoint(2));

			_cachedRobot->_targetPoint = _robot->_targetPoint;

			// Create Transformation Matrix to transmit
			igtl::PointMessage::Pointer targetMsg = igtl::PointMessage::New();
			targetMsg->SetDeviceName("target_point");
			targetPoint->SetName("target_point");
			targetMsg->AddPointElement(targetPoint);
			targetMsg->Pack();
			socket->Send(targetMsg->GetPackPointer(), targetMsg->GetPackSize());
		}

		//  SEND ROBOT Probe -- Cannula To Treatment
		if (_robot->_probe._cannulaToTreatment != _cachedRobot->_probe._cannulaToTreatment || _retransmit)
		{
			// Convert Eigen Vector to IGT Point and update the cached robot
			string cannulaToTreatment = to_string(_robot->_probe._cannulaToTreatment);
			_cachedRobot->_probe._cannulaToTreatment = _robot->_probe._cannulaToTreatment;

			// Create Transformation Matrix to transmit
			igtl::StringMessage::Pointer cannulaMsg = igtl::StringMessage::New();
			cannulaMsg->SetDeviceName("cannula_to_treatment");
			cannulaMsg->SetString(cannulaToTreatment.c_str());
			cannulaMsg->Pack();
			socket->Send(cannulaMsg->GetPackPointer(), cannulaMsg->GetPackSize());
		}

		//  SEND ROBOT Probe -- Treatment To Tip
		if (_robot->_probe._treatmentToTip != _cachedRobot->_probe._treatmentToTip || _retransmit)
		{
			// Convert Eigen Vector to IGT Point and update the cached robot
			string treatmentToTip = to_string(_robot->_probe._treatmentToTip);
			_cachedRobot->_probe._treatmentToTip = _robot->_probe._treatmentToTip;

			// Create Transformation Matrix to transmit
			igtl::StringMessage::Pointer treamentTipMsg = igtl::StringMessage::New();
			treamentTipMsg->SetDeviceName("treatment_to_tip");
			treamentTipMsg->SetString(treatmentToTip.c_str());
			treamentTipMsg->Pack();
			socket->Send(treamentTipMsg->GetPackPointer(), treamentTipMsg->GetPackSize());
		}

		//  SEND ROBOT Probe -- Robot To Entry
		if (_robot->_probe._robotToEntry != _cachedRobot->_probe._robotToEntry || _retransmit)
		{
			// Convert Eigen Vector to IGT Point and update the cached robot
			string robotToEntry = to_string(_robot->_probe._robotToEntry);
			_cachedRobot->_probe._robotToEntry = _robot->_probe._robotToEntry;

			// Create Transformation Matrix to transmit
			igtl::StringMessage::Pointer robotEntryMsg = igtl::StringMessage::New();
			robotEntryMsg->SetDeviceName("robot_to_entry");
			robotEntryMsg->SetString(robotToEntry.c_str());
			robotEntryMsg->Pack();
			socket->Send(robotEntryMsg->GetPackPointer(), robotEntryMsg->GetPackSize());
		}

		//  SEND ROBOT Probe -- Robot To Treatment at Home
		if (_robot->_probe._robotToTreatmentAtHome != _cachedRobot->_probe._robotToTreatmentAtHome || _retransmit)
		{
			// Convert Eigen Vector to IGT Point and update the cached robot
			string robotToTreatmentAtHome = to_string(_robot->_probe._robotToTreatmentAtHome);
			_cachedRobot->_probe._robotToTreatmentAtHome = _robot->_probe._robotToTreatmentAtHome;

			// Create Transformation Matrix to transmit
			igtl::StringMessage::Pointer robotToTreatmentAtHomeMsg = igtl::StringMessage::New();
			robotToTreatmentAtHomeMsg->SetDeviceName("robot_treatment_home"); // Due to 20 character limit full variable name could not be used
			robotToTreatmentAtHomeMsg->SetString(robotToTreatmentAtHome.c_str());
			robotToTreatmentAtHomeMsg->Pack();
			socket->Send(robotToTreatmentAtHomeMsg->GetPackPointer(), robotToTreatmentAtHomeMsg->GetPackSize());
		}

		// ==============================================================================================
		// **********************************************************************************************
		// ==============================================================================================
		// SEND ROBOT JOINT POSE -- CRTK
		vector<Motor *> motors = _robot->ListMotors();
		vector<Motor *> cached_motors = _cachedRobot->ListMotors();

		// Position difference
		bool detected_pos_diff = false;
		for (unsigned int i = 0; i < motors.size(); i++)
		{
			if (motors[i]->GetEncoderPositionTicks() != cached_motors[i]->GetEncoderPositionTicks())
			{
				detected_pos_diff = true;
				i = motors.size();
			}
		}

		// Set-point difference
		bool detected_setpoint_diff = false;
		for (unsigned int i = 0; i < motors.size(); i++)
		{
			if (motors[i]->_setpoint != cached_motors[i]->_setpoint)
			{
				detected_setpoint_diff = true;
				i = motors.size();
			}
		}

		// Velocity difference
		bool detected_vel_diff = false;
		for (unsigned int i = 0; i < motors.size(); i++)
		{
			if (motors[i]->GetEncoderVelocity() != cached_motors[i]->GetEncoderVelocity())
			{
				detected_vel_diff = true;
				i = motors.size();
			}
		}

		// If a Joint Space Position difference has been detected
		if (detected_pos_diff || _retransmit)
		{
			// cout << "Joint difference detected" << endl;
			// Send the Joint Space information as a string
			string joint_space = "";
			for (unsigned int i = 0; i < motors.size(); i++)
			{
				joint_space += to_string(motors[i]->GetEncoderPositionUnit());
				joint_space += ",";
				cached_motors[i]->_encoder._pos = motors[i]->GetEncoderPositionTicks();
			}

			if (joint_space.length() > 0)
			{
				// Send the result over OpenIGTLink
				// Create String to transmit
				igtl::StringMessage::Pointer jointPoseMsg = igtl::StringMessage::New();
				// jointPoseMsg->SetDeviceName("neuro_joint_pose"); // Due to 20 character limit full variable name could not be used
				jointPoseMsg->SetDeviceName("measured_jp");
				jointPoseMsg->SetString(joint_space.c_str());
				jointPoseMsg->Pack();
				socket->Send(jointPoseMsg->GetPackPointer(), jointPoseMsg->GetPackSize());

				cout << "TRANSMITTED JOINT SPACE STRING:" << endl;
				cout << joint_space << endl;
			}
		}

		// If a Joint Space Position difference has been detected
		if (detected_setpoint_diff || _retransmit)
		{
			// cout << "Joint difference detected" << endl;
			// Send the Joint Space information as a string
			string joint_space_setpoints = "";
			for (unsigned int i = 0; i < motors.size(); i++)
			{
				joint_space_setpoints += to_string(motors[i]->_setpoint);
				joint_space_setpoints += ",";
				cached_motors[i]->_setpoint = motors[i]->_setpoint;
			}

			if (joint_space_setpoints.length() > 0 || _retransmit)
			{
				// Send the result over OpenIGTLink
				// Create String to transmit
				igtl::StringMessage::Pointer jointPoseSetpointMsg = igtl::StringMessage::New();
				jointPoseSetpointMsg->SetDeviceName("desired_jp");
				jointPoseSetpointMsg->SetString(joint_space_setpoints.c_str());
				jointPoseSetpointMsg->Pack();
				socket->Send(jointPoseSetpointMsg->GetPackPointer(), jointPoseSetpointMsg->GetPackSize());

				cout << "TRANSMITTED JOINT SPACE STRING:" << endl;
				cout << joint_space_setpoints << endl;
			}
		}

		// If a Joint Space Velocity difference has been detected
		if (detected_vel_diff || _retransmit)
		{
			// cout << "Joint difference detected" << endl;
			// Send the Joint Space information as a string
			string joint_space_vel = "";
			for (unsigned int i = 0; i < motors.size(); i++)
			{
				joint_space_vel += to_string(motors[i]->GetEncoderVelocity());
				joint_space_vel += ",";
				cached_motors[i]->_encoder._vel = motors[i]->GetEncoderVelocity();
			}

			if (joint_space_vel.length() > 0)
			{
				// Send the result over OpenIGTLink
				// Create String to transmit
				igtl::StringMessage::Pointer jointPoseVelMsg = igtl::StringMessage::New();
				jointPoseVelMsg->SetDeviceName("measured_jv");
				jointPoseVelMsg->SetString(joint_space_vel.c_str());
				jointPoseVelMsg->Pack();
				socket->Send(jointPoseVelMsg->GetPackPointer(), jointPoseVelMsg->GetPackSize());

				cout << "TRANSMITTED JOINT SPACE STRING:" << endl;
				cout << joint_space_vel << endl;
			}
		}

		_retransmit = false;
	}

	// ==============================================================================================
	// **********************************************************************************************
	// ==============================================================================================
}

void OpenIGTLink::DisconnectSocket()
{
	socket->CloseSocket();
}

Eigen::Matrix4d OpenIGTLink::ReceiveTransform(igtl::Socket *socket, igtl::MessageHeader *header)
{
	// Create a message buffer to receive transform data
	igtl::TransformMessage::Pointer transMsg;
	transMsg = igtl::TransformMessage::New();
	transMsg->SetMessageHeader(header);
	transMsg->AllocatePack();

	// Receive transform data from the socket
	socket->Receive(transMsg->GetPackBodyPointer(),
					transMsg->GetPackBodySize());

	// Deserialize the transform data, If you want to skip CRC check, call Unpack() without argument.
	int c = transMsg->Unpack();

	// Unpack the message body
	Eigen::Matrix4d unpackedTransform = Eigen::Matrix4d::Identity();
	if (c & igtl::MessageHeader::UNPACK_BODY)
	{
		// Retrieve the transform data
		igtl::Matrix4x4 incomingTransform;
		transMsg->GetMatrix(incomingTransform);

		for (int i = 0; i < 4; i++)
		{
			for (int j = 0; j < 4; j++)
			{
				unpackedTransform(i, j) = incomingTransform[i][j];
			}
		}

		return unpackedTransform;
	}

	return unpackedTransform;
}

string OpenIGTLink::ReceiveString(igtl::Socket *socket, igtl::MessageHeader *header)
{

	// Create a message buffer to receive transform data
	igtl::StringMessage::Pointer strMsg;
	strMsg = igtl::StringMessage::New();
	strMsg->SetMessageHeader(header);
	strMsg->AllocatePack();

	// Receive transform data from the socket
	socket->Receive(strMsg->GetPackBodyPointer(),
					strMsg->GetPackBodySize());

	// Deserialize the string data
	// If you want to skip CRC check, call Unpack() without argument.
	int c = strMsg->Unpack();
	string stringMessage = "";

	if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
	{
		stringMessage = strMsg->GetString();
	}
	return stringMessage;
}

int OpenIGTLink::ReceiveStatus(igtl::Socket *socket, igtl::MessageHeader *header)
{

	// Create a message buffer to receive transform data
	igtl::StatusMessage::Pointer statusMsg;
	statusMsg = igtl::StatusMessage::New();
	statusMsg->SetMessageHeader(header);
	statusMsg->AllocatePack();

	// Receive transform data from the socket
	socket->Receive(statusMsg->GetPackBodyPointer(),
					statusMsg->GetPackBodySize());

	// Deserialize the string data
	int c = statusMsg->Unpack();

	if (c & igtl::MessageHeader::UNPACK_BODY) // if CRC check is OK
	{
		// Retrive the status data

		int statusCode = statusMsg->GetCode();
		return statusCode;
	}
	return 0;
}

vector<int> OpenIGTLink::ReceiveArray(igtl::Socket *socket, igtl::MessageHeader *header)
{
	// Define this when the OpenIGT Library allows for arrays....
	vector<int> my_array = {0, 0, 0, 0, 0, 0, 0, 0};
	return my_array;
}
