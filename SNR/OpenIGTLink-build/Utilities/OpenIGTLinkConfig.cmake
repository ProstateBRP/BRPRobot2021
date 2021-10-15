#-----------------------------------------------------------------------------
#
# OpenIGTLinkConfig.cmake - OpenIGTLink CMake configuration file for external projects.
#
# This file is configured by OpenIGTLink and used by the UseOpenIGTLink.cmake module
# to load OpenIGTLink's settings for an external project.

# Compute the installation prefix from this OpenIGTLinkConfig.cmake file location.
GET_FILENAME_COMPONENT(OpenIGTLink_INSTALL_PREFIX "${CMAKE_CURRENT_LIST_FILE}" PATH)
GET_FILENAME_COMPONENT(OpenIGTLink_INSTALL_PREFIX "${OpenIGTLink_INSTALL_PREFIX}" PATH)
GET_FILENAME_COMPONENT(OpenIGTLink_INSTALL_PREFIX "${OpenIGTLink_INSTALL_PREFIX}" PATH)
GET_FILENAME_COMPONENT(OpenIGTLink_INSTALL_PREFIX "${OpenIGTLink_INSTALL_PREFIX}" PATH)
GET_FILENAME_COMPONENT(OpenIGTLink_INSTALL_PREFIX "${OpenIGTLink_INSTALL_PREFIX}" PATH)

# The OpenIGTLink include file directories.
SET(OpenIGTLink_INCLUDE_DIRS "${OpenIGTLink_INSTALL_PREFIX}/include/igtl")

# The OpenIGTLink library directories.
SET(OpenIGTLink_LIBRARY_DIRS "${OpenIGTLink_INSTALL_PREFIX}/lib/igtl")

# The C and C++ flags added by OpenIGTLink to the cmake-configured flags.
SET(OpenIGTLink_REQUIRED_C_FLAGS "")
SET(OpenIGTLink_REQUIRED_CXX_FLAGS "")
SET(OpenIGTLink_REQUIRED_LINK_FLAGS "")

# The OpenIGTLink Library version number
SET(OpenIGTLink_VERSION_MAJOR "3")
SET(OpenIGTLink_VERSION_MINOR "1")
SET(OpenIGTLink_VERSION_PATCH "0")

# The OpenIGTLink Protocol version number
SET(OpenIGTLink_PROTOCOL_VERSION "3")

# The location of the UseOpenIGTLink.cmake file.
SET(OpenIGTLink_USE_FILE "${OpenIGTLink_INSTALL_PREFIX}/lib/igtl/cmake/igtl-3.1/UseOpenIGTLink.cmake")

# The build settings file.
SET(OpenIGTLink_BUILD_SETTINGS_FILE "${OpenIGTLink_INSTALL_PREFIX}/lib/igtl/cmake/igtl-3.1/OpenIGTLinkBuildSettings.cmake")

# Whether OpenIGTLink was built with shared libraries.
SET(OpenIGTLink_BUILD_SHARED "OFF")

# Whether OpenIGTLink was built with Tcl wrapping support.
SET(OpenIGTLink_CSWIG_TCL "")
SET(OpenIGTLink_CSWIG_PYTHON "")
SET(OpenIGTLink_CSWIG_JAVA "")

# Whether OpenIGTLink was built with video streaming library support
SET(OpenIGTLink_USE_H264 OFF)
SET(OpenIGTLink_USE_VP9 OFF)
SET(OpenIGTLink_USE_X265 OFF)
SET(OpenIGTLink_USE_OpenHEVC OFF)
SET(OpenIGTLink_USE_AV1 OFF)
SET(OpenIGTLink_ENABLE_VIDEOSTREAMING OFF)
SET(OpenIGTLink_USE_WEBSOCKET OFF)

# Path to CableSwig configuration used by OpenIGTLink.
SET(OpenIGTLink_CableSwig_DIR "")

# A list of all libraries for OpenIGTLink.  Those listed here should
# automatically pull in their dependencies.
SET(OpenIGTLink_LIBRARIES OpenIGTLink)

# The OpenIGTLink library targets.
SET(OpenIGTLink_LIBRARY_TARGETS_FILE "${OpenIGTLink_INSTALL_PREFIX}/lib/igtl/cmake/igtl-3.1/OpenIGTLinkTargets.cmake")
include(${OpenIGTLink_LIBRARY_TARGETS_FILE})
