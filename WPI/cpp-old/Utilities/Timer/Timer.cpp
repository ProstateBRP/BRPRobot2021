//============================================================================
// Name        : Timer.cpp
// Author      : Farid Tavakkolmoghaddam
// Description : This file is used to profile the code
//============================================================================

#include "Timer.hpp"
#include <chrono>

Timer::Timer() {
	_usStart = 0;
	_usFinish = 0;
}

void Timer::tic(){
	//clock_gettime(CLOCK_MONOTONIC, &_clockStart);
	_clockStart = std::chrono::steady_clock::now();
	//_usStart = _clockStart.tv_sec*1000000 + _clockStart.tv_nsec/1000;
	//_usStart = 0;
}

void Timer::toc(){
	//clock_gettime(CLOCK_MONOTONIC, &_clockFinish);
	_clockFinish = std::chrono::steady_clock::now();
	//'_usFinish = _clockFinish.tv_sec*1000000 + _clockFinish.tv_nsec/1000;
	//_usFinish = 0;
}

unsigned long long Timer::time(){
	//return _usFinish - _usStart;
	return std::chrono::duration_cast<std::chrono::microseconds>(_clockStart - _clockFinish).count();
}


