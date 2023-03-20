# pragma once

#include <Eigen/Dense>
#include <iostream>
#include <cmath>
#include <vector>
#include <Eigen/QR>
#include <string.h>
enum class FitType
{
    LINEAR,
    CUBIC
};

enum class DesiredPlane
{
    XY,
    ZY
};

class PolyFit
{
public:
    PolyFit(std::string);
    // Functions
    int Fit(const std::vector<Eigen::Vector3d> &, int = 3);
    int CubicFit(int = 3);
    int LinearFit();
    double CalcAngle();
    // Attributes
    std::vector<double> coeffs{0, 0, 0};
    FitType fit_type{FitType::LINEAR};
    int x_idx{0}, y_idx{1};
    std::vector<double> x_data{};
    std::vector<double> y_data{};
    DesiredPlane desired_plane;
};