# Needle Trajectory Visualization Script Documentation

## Overview

`Visualize_Needle_Trajectory.m` is a MATLAB visualization and verification script designed to test and demonstrate the `Generate_Needle_Trajectory` function, which is the inverse function of `Cal_k_P_tt_theta_d`. This script generates needle trajectories based on curvature and target angle parameters, visualizes them in multiple views, and verifies the consistency between the forward and inverse functions.

## Purpose

The script serves two main purposes:

1. **Visualization**: Generate and display needle trajectories for different curvature and angle configurations
2. **Verification**: Validate that the inverse function (`Generate_Needle_Trajectory`) correctly produces trajectories that can be used to recover the original curvature and angle parameters using the forward function (`Cal_k_P_tt_theta_d`)

## Key Components

### 1. Path Setup

The script automatically adds required paths to access:
- `R_axis` class (for rotation axis enumeration)
- Functions directory (for `Cal_Ptb1_Ttb`, `Cal_Rotation_Matrix`, `Cal_k_P_tt_theta_d`)

```matlab
script_dir = fileparts(mfilename('fullpath'));
addpath(fullfile(script_dir, '..', 'classes'));
addpath(script_dir);
```

### 2. Test Cases

The script defines three test cases with different curvature and angle parameters:

#### Test Case 1: Moderate Curvature
- **Curvature (k)**: 0.001 mm⁻¹
- **Target Angle (θ_d)**: 45° (π/4 radians)
- **Z Range**: 0 to 100 mm with 1 mm step
- **Initial Position**: [0, 0, 0] mm

#### Test Case 2: High Curvature
- **Curvature (k)**: 0.002 mm⁻¹
- **Target Angle (θ_d)**: 90° (π/2 radians)
- **Z Range**: 0 to 80 mm with 1 mm step
- **Initial Position**: [0, 0, 0] mm

#### Test Case 3: Low Curvature (Nearly Straight)
- **Curvature (k)**: 0.0001 mm⁻¹
- **Target Angle (θ_d)**: 0° (0 radians)
- **Z Range**: 0 to 100 mm with 1 mm step
- **Initial Position**: [0, 0, 0] mm

### 3. Trajectory Generation

For each test case, the script calls `Generate_Needle_Trajectory` to compute the needle trajectory:

```matlab
trajectory = Generate_Needle_Trajectory(k, theta_d, z_range, initial_pos);
```

This function:
- Takes curvature `k` and target angle `theta_d` as inputs
- Generates a trajectory along the z-axis (insertion direction)
- Returns an N×3 matrix of [x, y, z] positions

### 4. Visualization

The script creates a figure with four subplots showing different views of the trajectories:

#### Subplot 1: 3D Trajectory Plot
- Displays all three trajectories in 3D space
- Shows the full spatial path of the needle
- Includes axis labels and legend with curvature and angle information

#### Subplot 2: X-Y Projection
- Projects trajectories onto the X-Y plane
- Shows the lateral deviation of the needle
- Demonstrates how `theta_d` affects the direction in the X-Y plane

#### Subplot 3: Y-Z Projection (Circular Arc)
- Projects trajectories onto the Y-Z plane
- Shows the circular arc shape of the curved trajectory
- Illustrates the relationship between curvature and arc radius

#### Subplot 4: X-Z Projection
- Projects trajectories onto the X-Z plane
- Shows the side view of the needle path
- Useful for understanding the 3D shape of the trajectory

All plots include:
- Grid lines for easier reading
- Equal axis scaling (`axis equal`)
- Color-coded trajectories (blue, red, green)
- Legend with curvature and angle values

### 5. Verification Test

The script performs a forward-inverse consistency check for each test case:

#### Process:
1. **Select Target Point**: Chooses a point from the generated trajectory (middle point)
2. **Set Initial Needle Pose**: Creates initial needle pose at the trajectory start position
   - Assumes initial orientation: γ=0, φ=0, θ=0
3. **Calculate Transformation Matrix**: Uses `Cal_Ptb1_Ttb` to compute the transformation matrix `T_tb`
4. **Forward Calculation**: Uses `Cal_k_P_tt_theta_d` to calculate curvature and angle from the target position
5. **Compare Results**: Compares calculated values with original input parameters

#### Output:
For each test case, the script prints:
- Input parameters (k, θ_d)
- Trajectory statistics (number of points, start/end positions)
- Calculated values from forward function
- Error summaries for both curvature and angle

#### Important note on sign/angle conventions

In this repository, the forward function `Cal_k_P_tt_theta_d` may return results that are **equivalent but not numerically identical** to the inputs used in `Generate_Needle_Trajectory`, due to sign and coordinate-frame conventions.

It is common to observe the following relationship:

- \(k_{calc} \approx -k_{in}\)
- \(\theta_{d,calc} \approx \theta_{d,in} + \pi\)

These two parameter sets can describe the **same physical trajectory** under a different sign convention. Downstream control code in this repo also applies `abs(k)` (see `Matlab/classes/Robot.m`), which indicates curvature is treated as a magnitude.

For this reason, the verification script reports both:

- **Direct comparison**: \((k_{calc}, \theta_{d,calc})\) vs \((k_{in}, \theta_{d,in})\)
- **Equivalent comparison**: \((-k_{calc}, \theta_{d,calc}-\pi)\) vs \((k_{in}, \theta_{d,in})\)

## Mathematical Background

### Inverse Function Principle

The `Generate_Needle_Trajectory` function implements the inverse of the equations used in `Cal_k_P_tt_theta_d`:

1. **Equation (8) Inverse**: Radius = 1/k
   - Converts curvature to radius

2. **Equation (7) Inverse**: Solving for y given z and radius
   - Original: `Radius = y/2 + z²/(2y)`
   - Rearranged: `y² - 2·Radius·y + z² = 0`
   - Solution: `y = Radius ± √(Radius² - z²)`

3. **Rotation**: Applies rotation matrix based on `theta_d` to orient the trajectory in the X-Y plane

### Coordinate System

- **Z-axis**: Needle insertion direction (forward motion)
- **X-Y plane**: Lateral plane perpendicular to insertion
- **theta_d**: Angle in X-Y plane defining the direction of curvature

## Usage

To run the visualization script:

```matlab
Visualize_Needle_Trajectory
```

The script will:
1. Generate trajectories for all three test cases
2. Display visualization plots
3. Print verification results to the command window

## Expected Output

### Visual Output
- A figure window with four subplots showing different views of the trajectories
- Color-coded trajectories for easy comparison

### Console Output
- Detailed information for each test case including:
  - Input parameters
  - Trajectory statistics
  - Calculated values from forward function
  - Error analysis

## Dependencies

The script requires the following functions and classes:
- `Generate_Needle_Trajectory.m` - Inverse function for trajectory generation
- `Cal_k_P_tt_theta_d.m` - Forward function for curvature/angle calculation
- `Cal_Ptb1_Ttb.m` - Transformation matrix calculation
- `Cal_Rotation_Matrix.m` - Rotation matrix generation
- `R_axis.m` - Rotation axis enumeration class

## Notes

- The verification test assumes initial orientation angles (γ, φ, θ) are all zero
- The script uses the middle point of each trajectory for verification
- Error percentages are calculated to assess the accuracy of the inverse function
- The visualization uses equal axis scaling to maintain proper aspect ratios

## Applications

This script is useful for:
- **Testing**: Validating the correctness of the inverse trajectory generation function
- **Visualization**: Understanding how curvature and angle parameters affect needle paths
- **Debugging**: Identifying issues in trajectory calculation algorithms
- **Education**: Demonstrating the relationship between control parameters and needle trajectories
