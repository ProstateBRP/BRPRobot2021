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
  NavigationDynamicCommunicationTest.cxx
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

OPTION(SCRIPT_AS_MAIN "Compiling script.cxx as main" OFF)
IF(SCRIPT_AS_MAIN)
    ADD_DEFINITIONS(-DMAIN)
    ADD_EXECUTABLE(script ./script.cxx)
    TARGET_LINK_LIBRARIES(script OpenIGTLink)
ELSE()
    ADD_EXECUTABLE(NavigationTestSimulator ${NAVIGATION_SIM_SOURCE} ./script.cxx)
    TARGET_LINK_LIBRARIES(NavigationTestSimulator OpenIGTLink)
ENDIF()
