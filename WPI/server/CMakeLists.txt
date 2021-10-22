PROJECT(BRPProstateRobotTest)

cmake_minimum_required(VERSION 2.4)
if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

find_package(OpenIGTLink REQUIRED)

include(${OpenIGTLink_USE_FILE})

set(NAVIGATION_SIM_SOURCE
  TestBase.cxx
  NavigationTestBase.cxx
  NavigationTestSimulator.cxx
  NavigationNormalOperationTest.cxx
  NavigationStartUpErrorTest.cxx
  NavigationCalibrationErrorTest.cxx
  NavigationTargetingWithoutCalibrationTest.cxx
  NavigationOutOfRangeTest.cxx
  NavigationStopDuringOperationTest.cxx
  NavigationEmergencyStopDuringOperationTest.cxx
  NavigationMoveToWithoutTargetTest.cxx
  NavigationAccidentalCommandDuringManualModeTest.cxx
  NavigationHardwareErrorDuringOperationTest.cxx
)

set(ROBOT_SIM_SOURCE
  RobotSimulatorPhaseBase.cxx
  RobotSimulatorUndefinedPhase.cxx
  RobotSimulatorStartUpPhase.cxx
  RobotSimulatorPlanningPhase.cxx
  RobotSimulatorCalibrationPhase.cxx
  RobotSimulatorTargetingPhase.cxx
  RobotSimulatorMoveToTargetPhase.cxx
  RobotSimulatorManualPhase.cxx
  RobotSimulatorStopPhase.cxx
  RobotSimulatorEmergencyPhase.cxx
  RobotTestSimulator.cxx
  TestBase.cxx
  RobotStatus.cxx
)

ADD_EXECUTABLE(RobotTestSimulator  ${ROBOT_SIM_SOURCE})
TARGET_LINK_LIBRARIES(RobotTestSimulator OpenIGTLink)

ADD_EXECUTABLE(NavigationTestSimulator ${NAVIGATION_SIM_SOURCE})
TARGET_LINK_LIBRARIES(NavigationTestSimulator OpenIGTLink)
