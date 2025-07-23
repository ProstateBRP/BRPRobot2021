cmake_minimum_required(VERSION 3.1)

add_library(CurvSteering CurvSteering.cxx ../SteeringAlgorithm.cxx)

target_link_libraries(CurvSteering
    BicycleKinematics
)
