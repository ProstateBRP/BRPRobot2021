PROJECT(BRPProstateRobotTest)

cmake_minimum_required(VERSION 3.1)

if(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
endif(COMMAND cmake_policy)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG TRUE)
find_package(Threads REQUIRED)

# find_package(OpenIGTLink REQUIRED)
# include(${OpenIGTLink_USE_FILE})

set(EIGEN_DIR /usr/include/eigen3)
include_directories(${EIGEN_DIR})

add_subdirectory(./NeedleKinematics/)
add_subdirectory(./Robot/)
add_subdirectory(./Server/)
add_subdirectory(./SteeringAlgorithm/CurvSteering/)
add_subdirectory(./Utilities/Timer)
add_subdirectory(./Utilities/Logger)


set(ROBOT_SIM_SOURCE
  main.cxx
)

ADD_EXECUTABLE(RobotTest ${ROBOT_SIM_SOURCE})
TARGET_LINK_LIBRARIES(RobotTest 
Threads::Threads
OpenIGTLinkComm
Logger
Timer
Robot
BicycleKinematics
CurvSteering

)

