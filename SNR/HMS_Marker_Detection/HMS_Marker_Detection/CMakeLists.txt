cmake_minimum_required(VERSION 3.7.1)

set(MODULE_NAME HMS_Marker_Detection)
# same as the extension, so version is already set
MESSAGE(STATUS "CLI version = ${${MODULE_NAME_UPPER}_VERSION}")
#-----------------------------------------------------------------------------

#
# SlicerExecutionModel
#
find_package(SlicerExecutionModel REQUIRED)
include(${SlicerExecutionModel_USE_FILE})

#
# ITK
#
set(${PROJECT_NAME}_ITK_COMPONENTS
  ITKIOImageBase
  ITKIOTransformBase
  ITKSmoothing
)
find_package(ITK 4.6 COMPONENTS ${${PROJECT_NAME}_ITK_COMPONENTS} REQUIRED)
set(ITK_NO_IO_FACTORY_REGISTER_MANAGER 1) # See Libs/ITKFactoryRegistration/CMakeLists.txt
include(${ITK_USE_FILE})

#-----------------------------------------------------------------------------
# Module include directories
#

# Include ZFrame calibration headers
set(ZFrame_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/ZFrame")
set(ZFrameMatrices_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/ZFrame/newmat")

set(MODULE_INCLUDE_DIRECTORIES
 ${SlicerBaseCLI_SOURCE_DIR}
 ${SlicerBaseCLI_BINARY_DIR}
 ${ZFrame_INCLUDE_DIR}
 ${ZFrameMatrices_SOURCE_DIR}
 )

set(ZFrameMatrices_SRCS
  ${ZFrameMatrices_SOURCE_DIR}/newmat9.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmatrm.cpp
  ${ZFrameMatrices_SOURCE_DIR}/nm_misc.cpp
  ${ZFrameMatrices_SOURCE_DIR}/bandmat.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat1.cpp
  ${ZFrameMatrices_SOURCE_DIR}/solution.cpp
  ${ZFrameMatrices_SOURCE_DIR}/cholesky.cpp
  ${ZFrameMatrices_SOURCE_DIR}/hholder.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat2.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmatex.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat3.cpp
  ${ZFrameMatrices_SOURCE_DIR}/sort.cpp
  ${ZFrameMatrices_SOURCE_DIR}/evalue.cpp
  ${ZFrameMatrices_SOURCE_DIR}/jacobi.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat4.cpp
  ${ZFrameMatrices_SOURCE_DIR}/submat.cpp
  ${ZFrameMatrices_SOURCE_DIR}/example.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat5.cpp
  ${ZFrameMatrices_SOURCE_DIR}/svd.cpp
  ${ZFrameMatrices_SOURCE_DIR}/myexcept.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat6.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmatnl.cpp
  ${ZFrameMatrices_SOURCE_DIR}/fft.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat7.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newfft.cpp
  ${ZFrameMatrices_SOURCE_DIR}/newmat8.cpp
  ${ZFrameMatrices_SOURCE_DIR}/ZLinAlg.cxx
  )

set(MODULE_SRCS
  ${CMAKE_CURRENT_SOURCE_DIR}/ZFrame/Calibration.h
  ${CMAKE_CURRENT_SOURCE_DIR}/ZFrame/Calibration.cxx
  HMS_Marker_Detection.cxx
)

set(MODULE_TARGET_LIBRARIES
  ${ITK_LIBRARIES}
  )

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  TARGET_LIBRARIES  ${MODULE_TARGET_LIBRARIES}
  INCLUDE_DIRECTORIES ${MODULE_INCLUDE_DIRECTORIES}
  ADDITIONAL_SRCS ${MODULE_SRCS} ${ZFrameMatrices_SRCS}
  )

#-----------------------------------------------------------------------------
# Copy the frame marker file to the build directory
MESSAGE(STATUS "CLI: Copying marker config file, source = ${CMAKE_CURRENT_SOURCE_DIR}, bin = ${CMAKE_CURRENT_BINARY_DIR}")
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/markers.csv
	${CMAKE_CURRENT_BINARY_DIR}/markers.csv
	COPYONLY)
# Install/package
MESSAGE(STATUS "Install share directory = ${Slicer_INSTALL_SHARE_DIR}")
install(
 FILES markers.csv
 DESTINATION ${Slicer_INSTALL_SHARE_DIR}/Config
 COMPONENT Runtime
 )

#-----------------------------------------------------------------------------
# Add the CLI executable to the export set
install(TARGETS ${MODULE_NAME}
        EXPORT ${MODULE_NAME}Targets
	RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}" COMPONENT Runtime)

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
