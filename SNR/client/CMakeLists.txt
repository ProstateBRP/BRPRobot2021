PROJECT(BRPProstateRobotTest)
cmake_minimum_required(VERSION 2.4)

if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

find_package(OpenIGTLink REQUIRED)

include(${OpenIGTLink_USE_FILE})

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(NAVIGATION_TEST_SOURCE
  IGTControlBase.cxx
  NavigationIGTControlBase.cxx
  BridgeTesting/NavigationBridgeSimulator.cxx
  BridgTesting/NavigationNormalOperationTest.cxx
  BridgeTesting/NavigationStartUpErrorTest.cxx
  BridgeTesting/NavigationCalibrationErrorTest.cxx
  BridgeTesting/NavigationTargetingWithoutCalibrationTest.cxx
  BridgeTesting/NavigationOutOfRangeTest.cxx
  BridgeTesting/NavigationStopDuringOperationTest.cxx
  BridgeTesting/NavigationEmergencyStopDuringOperationTest.cxx
  BridgeTesting/NavigationMoveToWithoutTargetTest.cxx
  BridgeTesting/NavigationAccidentalCommandDuringManualModeTest.cxx
  BridgeTesting/NavigationHardwareErrorDuringOperationTest.cxx
)

set(NAVIGATION_RELEASE_SOURCE
  IGTControlBase.cxx
  NavigationIGTControlBase.cxx
  NavigationBridgeController.cxx
  NavigationBridge.cxx
)

# ADD_EXECUTABLE(test ${NAVIGATION_TEST_SOURCE} ./NavigationSlicerScript.cxx)
# TARGET_LINK_LIBRARIES(test OpenIGTLink)

ADD_EXECUTABLE(release ${NAVIGATION_RELEASE_SOURCE} ./NavigationSlicerScript.cxx)
TARGET_LINK_LIBRARIES(release OpenIGTLink)

# OPTION(SCRIPT_AS_MAIN "Compiling NavigationSlicerScript.cxx as main" OFF)
# IF(SCRIPT_AS_MAIN)
#   ADD_DEFINITIONS(-DMAIN)
#   ADD_EXECUTABLE(NavigationSlicerScript ./NavigationSlicerScript.cxx)
#   TARGET_LINK_LIBRARIES(NavigationSlicerScript OpenIGTLink)
# ENDIF()
