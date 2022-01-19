PROJECT(BRPProstateRobotTest)

cmake_minimum_required(VERSION 2.4)
if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

find_package(OpenIGTLink REQUIRED)

include(${OpenIGTLink_USE_FILE})

set(ROBOT_SIM_SOURCE
  main.cxx
  RobotPhaseBase.cxx
  RobotUndefinedPhase.cxx
  RobotStartUpPhase.cxx
  RobotPlanningPhase.cxx
  RobotCalibrationPhase.cxx
  RobotTargetingPhase.cxx
  RobotMoveToTargetPhase.cxx
  RobotManualPhase.cxx
  RobotStopPhase.cxx
  RobotEmergencyPhase.cxx
  RobotCommunicationBase.cxx
  RobotStatus.cxx
  ../Utilities/Logger/Logger.cpp
  ../Utilities/Timer/Timer.cpp
)

ADD_EXECUTABLE(RobotTest  ${ROBOT_SIM_SOURCE})
TARGET_LINK_LIBRARIES(RobotTest OpenIGTLink)
