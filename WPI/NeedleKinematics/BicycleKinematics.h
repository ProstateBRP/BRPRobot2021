#ifndef _BICYCLEKINEMATICS_H_
#define _BICYCLEKINEMATICS_H_
#include <math.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <vector>
#include "Eigen/Dense"

class BicycleKinematics
{
public:
    // Constructor
    BicycleKinematics();

    // Member functions
    Eigen::Matrix4d ForwardKinematicsBicycleModel(const Eigen::Matrix4d &, const double &, const double &);
    Eigen::Matrix4d ApplyRotationEulerAngles(const Eigen::Matrix4d &, const Eigen::Vector3d &);
    Eigen::Matrix4d ApplyRotationFixedAngles(const Eigen::Matrix4d &, const Eigen::Vector3d &);
    Eigen::Matrix4d RotateAboutZ(const Eigen::Matrix4d &, const double &);
    Eigen::Matrix4d CalcSpecialEuclideanMatrix(const Eigen::Matrix4d &);
    Eigen::Matrix3d CalcSpecialOrthagonalMatrix(const Eigen::Matrix3d &);
    Eigen::Vector3d ConvertToSpecialOrthagonalVector(const Eigen::Matrix3d &);
    Eigen::Matrix4d ConvertToSpecialEuclideanMatrix(const Eigen::VectorXd &);
    Eigen::Matrix3d ConvertToSpecialOrthagonalMatrix(const Eigen::Vector3d &);

    // Member attributes
    Eigen::Vector3d e1;
    Eigen::Vector3d e2;
    Eigen::Vector3d e3;
    double l2;
    double max_curvature;
    Eigen::VectorXd v1;
    Eigen::VectorXd v2;
};

#endif /*_BICYCLEKINEMATICS_H_*/