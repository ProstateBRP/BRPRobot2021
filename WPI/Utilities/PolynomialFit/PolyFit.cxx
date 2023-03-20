#include "PolyFit.h"

PolyFit::PolyFit(std::string plane)
{
    if (plane == "ZY" || plane == "zy")
    {
        desired_plane = DesiredPlane::ZY;
        x_idx = 2;
        y_idx = 1;
    }
    else if (plane == "XY" || plane == "xy")
    {
        desired_plane = DesiredPlane::XY;
        x_idx = 0;
        y_idx = 1;
    }
    else
    {
        std::cerr << "Invalid plane! Check your input argument.\n";
    }
}

// Calculate the coefficients of a kth order polynomial given a set of data points
int PolyFit::Fit(const std::vector<Eigen::Vector3d> &data_pts, int order)
{
    // Determine the fit type based on the data size
    if (data_pts.size() < 2)
    {
        std::cerr << "Invalid Operation!" << std::endl;
        return 0;
    }
    else if (data_pts.size() > 2)
    {
        fit_type = FitType::CUBIC;
    }
    // Clear up the buffer
    x_data.clear();
    y_data.clear();

    // Extract the data points
    Eigen::Vector3d data_pt;
    // Populate the x and y points
    for (size_t i = 0; i < data_pts.size(); i++)
    {
        x_data.push_back(data_pts.at(i)(x_idx));
        y_data.push_back(data_pts.at(i)(y_idx));
    }
    // Perform fit
    if (fit_type == FitType::LINEAR)
    {
        LinearFit();
    }
    else
    {
        CubicFit();
    }
}

int PolyFit::LinearFit()
{
    // Clean up the coeffs first
    coeffs.clear();
    // Calculate the slope and push back
    coeffs.push_back((y_data.at(1) - y_data.at(0)) / (x_data.at(1) - x_data.at(0)));
    return 1;
}

// Perform 3rd order polynomial fit (Cubic)
// y = (a3 * x^3) + (a2 * x^2) + (a1 * x) + a0 ;
int PolyFit::CubicFit(int order)
{
    // Clean up the coeffs first
    coeffs.clear();
    // Create Matrix Placeholder of size n x k, n= number of data points,
    // k = order of polynomial(default = 3 for cubic polynomial)
    Eigen::MatrixXd T(x_data.size(), order + 1);
    Eigen::VectorXd V = Eigen::VectorXd::Map(&y_data.front(), y_data.size());
    Eigen::VectorXd result;

    // Populate the matrix
    for (size_t i = 0; i < x_data.size(); ++i)
    {
        for (size_t j = 0; j < order + 1; ++j)
        {
            T(i, j) = pow(x_data.at(i), j);
        }
    }

    // Solve for linear least square fit
    result = T.householderQr().solve(V);
    coeffs.resize(order + 1);
    // coeffs.at(0) = a0, ... , coeffs.at(3) = a3
    for (int k = 0; k < order + 1; k++)
    {
        coeffs[k] = result[k];
    }

    return 1;
}

double PolyFit::CalcAngle()
{
    if (x_data.size() > 2)
    {
        if (fit_type == FitType::LINEAR)
        {
            // Find an arbitrary point based on the calculated slope.
            double x{1};
            double y = x * coeffs.at(0);
            return atan2(y, x);
        }
        // Cubic fit angle calculation
        else
        {
            // Calculate the derivative to find the slope at the last point
            // y' = (3 * a3 * x^2) + (2 * a2 * x) + (a1);
            const double x = x_data.back();
            const double y = y_data.back();
            double slope = (3 * coeffs.at(3) * pow(x, 2)) + (2 * coeffs.at(2) * x) + coeffs.at(1);
            double x0 = x - ((y) / (x - x0));
            return atan2(y, (x - x0));
        }
    }
    else
    {
        std::cerr << "Not enough data\n";
        return 0;
    }
}
