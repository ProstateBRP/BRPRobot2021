PROJECT(BRPRobot2021)

cmake_minimum_required(VERSION 3.1)

if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

find_package(OpenIGTLink REQUIRED)
include(${OpenIGTLink_USE_FILE})

ADD_SUBDIRECTORY(SNR/client)
ADD_SUBDIRECTORY(WPI/)
