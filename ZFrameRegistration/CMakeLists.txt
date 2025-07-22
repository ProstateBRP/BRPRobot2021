cmake_minimum_required(VERSION 3.5)

project(ZFrameRegistration)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/SlicerProstate/SlicerZFrameRegistration")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Junichi Tokuda (SPL), Christian Herz (SPL), Simon Di Maio (SPL), Longquan Chen (SPL), Andrey Fedorov (SPL), Franklin King (SNR), Rebecca Lisk (SNR)")
set(EXTENSION_DESCRIPTION "This extension provides support for procedures with ZFrame Registration")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/SlicerProstate/SlicerZFrameRegistration/master/ZFrameRegistration.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/SlicerProstate/SlicerZFrameRegistration/master/Screenshots/1.png https://raw.githubusercontent.com/SlicerProstate/SlicerZFrameRegistration/master/Screenshots/2.png")
set(EXTENSION_DEPENDS "SlicerDevelopmentToolbox")
#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ZFrameRegistration)
add_subdirectory(ZFrameRegistrationWithROI)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
