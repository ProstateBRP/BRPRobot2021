//============================================================================
// Name        : Logger.hpp
// Author      : Produced in the WPI AIM Lab
// Description : This file is used for logging information from the system to a text file
//============================================================================

#ifndef LOGGER_HPP_
#define LOGGER_HPP_

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#define HAVE_STRUCT_TIMESPEC
#pragma comment(lib,"pthreadVC2.lib")
#include <pthread.h>
#include "../Timer/Timer.hpp"

using namespace std;

#define LOG_LEVEL_DEBUG 0
#define LOG_LEVEL_INFO 1
#define LOG_LEVEL_WARNING 2
#define LOG_LEVEL_ERROR 3
#define LOG_LEVEL_CRITICAL 4
#define LOG_LEVEL_DATA 5

class Logger
{
public:
	//================ Constructor ================
	Logger();

	//================ Parameters =================
	// Parameters are initialized in constructor

	Timer _timer;
	string _filename;
	fstream _file; // for reading and writing to the file
	int _logLevelSeverity;
	int _currentLineNumber;
	std::string _actualTime;

	pthread_mutex_t logMutex;

	//================ Public Methods ==============
	string GetFileName();
	vector<vector<string>> ReadLogData(int numberOfLinesToRead);
	void SetLogLevel(int severity);
	void Log(string logData, int severity, bool printToConsole = false);
	// Overloaded method for loging events with the actual time
	void Log(string logData, string actual_time, int severity, bool printToConsole = false);
	void SetActualTime(std::string actualTime);
	string GetActualTime(){return this->_actualTime;}
	//======== Singleton Specific Methods ===========
	static Logger &GetInstance()
	{
		static Logger instance;
		return instance;
	}

	Logger(Logger const &) = delete;
	void operator=(Logger const &) = delete;
};

#endif /* LOGGER_HPP_ */
