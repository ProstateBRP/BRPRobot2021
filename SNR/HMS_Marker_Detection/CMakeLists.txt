cmake_minimum_required(VERSION 3.7.1)

set(MODULE_NAME HMS_Marker_Detection)
string(TOUPPER ${MODULE_NAME} MODULE_NAME_UPPER)
project(${MODULE_NAME})
set(${MODULE_NAME_UPPER}_MAJOR_VERSION 0)
set(${MODULE_NAME_UPPER}_MINOR_VERSION 3)
set(${MODULE_NAME_UPPER}_PATCH_VERSION 1)
set(${MODULE_NAME_UPPER}_VERSION
    ${${MODULE_NAME_UPPER}_MAJOR_VERSION}.${${MODULE_NAME_UPPER}_MINOR_VERSION}.${${MODULE_NAME_UPPER}_PATCH_VERSION})
if(POLICY CMP0048)
  set(_project_version VERSION ${${MODULE_NAME_UPPER}_VERSION})
endif()
MESSAGE(STATUS "Extension version = ${${MODULE_NAME_UPPER}_VERSION}")


#-----------------------------------------------------------------------------
# Extension meta-information
#----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/HMS_Marker_Detection")
set(EXTENSION_CATEGORY "ProstateBx")
set(EXTENSION_CONTRIBUTORS "Phill Marathakis, Nicole Aucoin (Harmonus Inc.)")
set(EXTENSION_DESCRIPTION "This is a extension to do marker detection.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/Harmonus/HMS_SlicerModule/master/Module_Resourses/Images/HarmonusIcon.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/CLIExtensionTemplate/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer 4.6 REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(HMS_Marker_Detection)
## NEXT_MODULE

#-----------------------------------------------------------------------------
# Set up configuration so that this cli can be used for testing without
# Slicer installation
export(TARGETS ${MODULE_NAME}
       FILE "${CMAKE_CURRENT_BINARY_DIR}/${MODULE_NAME}Targets.cmake"
       )
export(PACKAGE ${MODULE_NAME})

# Create the HMS_Marker_DetectionConfig.cmake file and HMS_Marker_DetectionConfigVersion files
# ... for the build tree
set(CONF_INCLUDE_DIRS "${PROJECT_SOURCE_DIR}" "${PROJECT_BINARY_DIR}")
configure_file(${MODULE_NAME}Config.cmake.in
  "${PROJECT_BINARY_DIR}/${MODULE_NAME}Config.cmake" @ONLY)
# ... for the install tree
set(CONF_INCLUDE_DIRS "\${${MODULE_NAME_UPPER}_CMAKE_DIR}/${REL_INCLUDE_DIR}")
configure_file(${MODULE_NAME}Config.cmake.in
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/${MODULE_NAME}Config.cmake" @ONLY)
# ... for both
configure_file(${MODULE_NAME}ConfigVersion.cmake.in
  "${PROJECT_BINARY_DIR}/${MODULE_NAME}ConfigVersion.cmake" @ONLY)

# Install the ${MODULE_NAME}Config.cmake and ${MODULE_NAME}ConfigVersion.cmake
install(FILES
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/${MODULE_NAME}Config.cmake"
  "${PROJECT_BINARY_DIR}/${MODULE_NAME}ConfigVersion.cmake"
  DESTINATION "${CMAKE_INSTALL_PREFIX}" COMPONENT Runtime)

# Install the export set for use with the install-tree
install(EXPORT ${MODULE_NAME}Targets DESTINATION
  "${CMAKE_INSTALL_PREFIX}" COMPONENT Runtime)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
