# Install script for directory: /Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source

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
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/igtl" TYPE FILE FILES
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_header.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_image.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_position.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_transform.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_types.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_util.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_capability.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_win32header.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMessageHandler.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMessageHandlerMacro.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlCapabilityMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlClientSocket.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlConditionVariable.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlCreateObjectFunction.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlFastMutexLock.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlImageMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlImageMessage2.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlLightObject.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMacro.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMath.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMessageBase.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMessageFactory.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMessageHeader.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMultiThreader.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMutexLock.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlObjectFactory.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlOSUtil.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlObject.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlObjectFactoryBase.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlPositionMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlServerSocket.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlSessionManager.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlSimpleFastMutexLock.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlSmartPointer.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlSocket.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlStatusMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlTimeStamp.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlTransformMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlTypes.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlWin32Header.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlWindows.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlCommon.h"
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
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlColorTableMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlImageMetaMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlLabelMetaMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlPointMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlTrackingDataMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlPolyDataMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlQuaternionTrackingDataMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlTrajectoryMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlStringMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlUnit.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlSensorMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlBindMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlNDArrayMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlCommandMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlQueryMessage.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_command.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlutil/igtl_query.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlMessageRTPWrapper.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlGeneralSocket.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlUDPClientSocket.h"
    "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink/Source/igtlUDPServerSocket.h"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xDevelopmentx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/igtl" TYPE STATIC_LIBRARY FILES "/Users/lisa/Desktop/BRPRobot2021/SNR/OpenIGTLink-build/lib/libOpenIGTLink.a")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/igtl/libOpenIGTLink.a" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/igtl/libOpenIGTLink.a")
    execute_process(COMMAND "/Library/Developer/CommandLineTools/usr/bin/ranlib" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/igtl/libOpenIGTLink.a")
  endif()
endif()

