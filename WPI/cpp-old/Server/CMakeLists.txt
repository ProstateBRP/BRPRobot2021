cmake_minimum_required(VERSION 3.1)

add_library(OpenIGTLinkComm
  OpenIGTLink.cxx
  RobotPhaseBase.cxx
  RobotCalibrationPhase.cxx
  RobotCommunicationBase.cxx
  RobotEmergencyPhase.cxx
  RobotManualPhase.cxx
  RobotMoveToTargetPhase.cxx
  RobotPlanningPhase.cxx
  RobotStartUpPhase.cxx
  RobotStatus.cxx
  RobotStopPhase.cxx
  RobotTargetingPhase.cxx
  RobotUndefinedPhase.cxx
)

TARGET_LINK_LIBRARIES(OpenIGTLinkComm OpenIGTLink)
