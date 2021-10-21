PROJECT(String)

cmake_minimum_required(VERSION 2.4)
if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

find_package(OpenIGTLink REQUIRED)

include(${OpenIGTLink_USE_FILE})


#ADD_EXECUTABLE(StringServer   StringServer.cxx)
#TARGET_LINK_LIBRARIES(StringServer OpenIGTLink)
OPTION(LISA_SCRIPT_MAIN "compiling LisaScript.cxx as main" OFF)
IF(LISA_SCRIPT_MAIN)
ADD_DEFINITIONS(-DMAIN)
ADD_EXECUTABLE(RebeccaClient LisaScript.cxx)
ELSE()
  ADD_EXECUTABLE(RebeccaClient RebeccaClient.cxx LisaScript.cxx)
ENDIF()


TARGET_LINK_LIBRARIES(RebeccaClient OpenIGTLink)
