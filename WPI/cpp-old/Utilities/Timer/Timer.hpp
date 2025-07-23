//============================================================================
// Name        : Timer.hpp
// Author      : Farid Tavakkolmoghaddam
// Description : This file is used to profile the code
//============================================================================

#ifndef TIMER_HPP_
#define TIMER_HPP_

#include <chrono>
#include <stdio.h>

class Timer {
public:
	//================ Constructor =================
	Timer();

	//================ Parameters =================
	// Parameters are declared in constructor
	//struct timespec _clockStart, _clockFinish;
	std::chrono::steady_clock::time_point _clockStart, _clockFinish;
	unsigned long long _usStart, _usFinish; //microseconds

	//================ Public Methods ==============
	void tic();
	void toc();
	unsigned long long time();
};

#endif /* TIMER_HPP_ */
