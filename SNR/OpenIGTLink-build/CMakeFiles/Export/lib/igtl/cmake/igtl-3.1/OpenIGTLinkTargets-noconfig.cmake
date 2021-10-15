#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "igtlutil" for configuration ""
set_property(TARGET igtlutil APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(igtlutil PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_NOCONFIG "C"
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/igtl/libigtlutil.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS igtlutil )
list(APPEND _IMPORT_CHECK_FILES_FOR_igtlutil "${_IMPORT_PREFIX}/lib/igtl/libigtlutil.a" )

# Import target "OpenIGTLink" for configuration ""
set_property(TARGET OpenIGTLink APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(OpenIGTLink PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_NOCONFIG "C;CXX"
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/igtl/libOpenIGTLink.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS OpenIGTLink )
list(APPEND _IMPORT_CHECK_FILES_FOR_OpenIGTLink "${_IMPORT_PREFIX}/lib/igtl/libOpenIGTLink.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
