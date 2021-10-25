PROJECT(String)

cmake_minimum_required(VERSION 2.4)
if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

find_package(OpenIGTLink REQUIRED)

include(${OpenIGTLink_USE_FILE})

OPTION(SCRIPT_AS_MAIN "Compiling script.cxx as main" OFF)
IF(SCRIPT_AS_MAIN)
    ADD_DEFINITIONS(-DMAIN)
    ADD_EXECUTABLE(script ./client/script.cxx)
    TARGET_LINK_LIBRARIES(script OpenIGTLink)
#ELSE()
#    ADD_EXECUTABLE(client   ./client/client.cxx ./client/script.cxx)
#    TARGET_LINK_LIBRARIES(client OpenIGTLink)
ELSE()
    ADD_EXECUTABLE(Client   ./client/main.cxx  ./client/Client.cxx ./client/script.cxx)
    TARGET_LINK_LIBRARIES(Client OpenIGTLink)
ENDIF()
