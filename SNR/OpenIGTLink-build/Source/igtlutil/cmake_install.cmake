# Install script for directory: /Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/Library/Developer/CommandLineTools/usr/bin/objdump")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xDevelopmentx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/igtl/igtlutil" TYPE FILE FILES
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_header.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_image.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_position.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_transform.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_types.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_util.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_capability.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_colortable.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_imgmeta.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_lbmeta.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_point.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_tdata.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_qtdata.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_trajectory.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_unit.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_sensor.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_string.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_ndarray.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_bind.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_qtrans.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_polydata.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_command.h"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xDevelopmentx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/igtl" TYPE STATIC_LIBRARY FILES "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink-build/lib/libigtlutil.a")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/igtl/libigtlutil.a" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/igtl/libigtlutil.a")
    execute_process(COMMAND "/Library/Developer/CommandLineTools/usr/bin/ranlib" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/igtl/libigtlutil.a")
  endif()
endif()

