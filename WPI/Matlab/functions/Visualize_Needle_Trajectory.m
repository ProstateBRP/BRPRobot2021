% Visualize_Needle_Trajectory  Visualization sample code for Generate_Needle_Trajectory
% This script tests the inverse function and visualizes the needle trajectory

clear; close all; clc;

% Add paths for required classes and functions
script_dir = fileparts(mfilename('fullpath'));
addpath(fullfile(script_dir, '..', 'classes')); % Add classes directory for R_axis
addpath(script_dir); % Add functions directory

% Helper functions (no toolboxes required)
wrapTo2Pi = @(a) mod(a, 2*pi);
angleDiff = @(a,b) abs(atan2(sin(a-b), cos(a-b))); % [0, pi]

%% Test Parameters
% Test case 1: Moderate curvature
k1 = 0.001; % curvature [1/mm] = 0.001 mm^-1
theta_d1 = pi/4; % 45 degrees
z_range1 = [0, 100, 1]; % z from 0 to 100 mm with 1 mm step
initial_pos1 = [0, 0, 0];

% Test case 2: High curvature
k2 = 0.002; % curvature [1/mm] = 0.002 mm^-1
theta_d2 = pi/2; % 90 degrees
z_range2 = [0, 80, 1]; % z from 0 to 80 mm with 1 mm step
initial_pos2 = [0, 0, 0];

% Test case 3: Low curvature (almost straight)
k3 = 0.0001; % curvature [1/mm] = 0.0001 mm^-1
theta_d3 = 0; % 0 degrees
z_range3 = [0, 100, 1]; % z from 0 to 100 mm with 1 mm step
initial_pos3 = [0, 0, 0];

%% Generate Trajectories
trajectory1 = Generate_Needle_Trajectory(k1, theta_d1, z_range1, initial_pos1);
trajectory2 = Generate_Needle_Trajectory(k2, theta_d2, z_range2, initial_pos2);
trajectory3 = Generate_Needle_Trajectory(k3, theta_d3, z_range3, initial_pos3);

%% Visualization
figure('Position', [100, 100, 1200, 800]);

% 3D plot
subplot(2, 2, 1);
plot3(trajectory1(:,1), trajectory1(:,2), trajectory1(:,3), 'b-', 'LineWidth', 2); hold on;
plot3(trajectory2(:,1), trajectory2(:,2), trajectory2(:,3), 'r-', 'LineWidth', 2);
plot3(trajectory3(:,1), trajectory3(:,2), trajectory3(:,3), 'g-', 'LineWidth', 2);
xlabel('X [mm]'); ylabel('Y [mm]'); zlabel('Z [mm]');
title('3D Needle Trajectories');
legend(sprintf('k=%.4f, θ_d=%.1f°', k1, theta_d1*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k2, theta_d2*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k3, theta_d3*180/pi), ...
       'Location', 'best');
grid on; axis equal;

% X-Y projection
subplot(2, 2, 2);
plot(trajectory1(:,1), trajectory1(:,2), 'b-', 'LineWidth', 2); hold on;
plot(trajectory2(:,1), trajectory2(:,2), 'r-', 'LineWidth', 2);
plot(trajectory3(:,1), trajectory3(:,2), 'g-', 'LineWidth', 2);
xlabel('X [mm]'); ylabel('Y [mm]');
title('X-Y Projection');
legend(sprintf('k=%.4f, θ_d=%.1f°', k1, theta_d1*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k2, theta_d2*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k3, theta_d3*180/pi), ...
       'Location', 'best');
grid on; axis equal;

% Y-Z projection
subplot(2, 2, 3);
plot(trajectory1(:,2), trajectory1(:,3), 'b-', 'LineWidth', 2); hold on;
plot(trajectory2(:,2), trajectory2(:,3), 'r-', 'LineWidth', 2);
plot(trajectory3(:,2), trajectory3(:,3), 'g-', 'LineWidth', 2);
xlabel('Y [mm]'); ylabel('Z [mm]');
title('Y-Z Projection (Circular Arc)');
legend(sprintf('k=%.4f, θ_d=%.1f°', k1, theta_d1*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k2, theta_d2*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k3, theta_d3*180/pi), ...
       'Location', 'best');
grid on; axis equal;

% X-Z projection
subplot(2, 2, 4);
plot(trajectory1(:,1), trajectory1(:,3), 'b-', 'LineWidth', 2); hold on;
plot(trajectory2(:,1), trajectory2(:,3), 'r-', 'LineWidth', 2);
plot(trajectory3(:,1), trajectory3(:,3), 'g-', 'LineWidth', 2);
xlabel('X [mm]'); ylabel('Z [mm]');
title('X-Z Projection');
legend(sprintf('k=%.4f, θ_d=%.1f°', k1, theta_d1*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k2, theta_d2*180/pi), ...
       sprintf('k=%.4f, θ_d=%.1f°', k3, theta_d3*180/pi), ...
       'Location', 'best');
grid on; axis equal;

sgtitle('Needle Trajectory Visualization', 'FontSize', 14, 'FontWeight', 'bold');

%% Verification: Check if we can recover k and theta_d from trajectory using original function
fprintf('\n=== Verification Test (Forward-Inverse Consistency) ===\n');

% Test Case 1: Verify inverse function using original function
fprintf('\nTest Case 1:\n');
fprintf('  Input: k = %.6f [1/mm], theta_d = %.4f [rad] (%.1f deg)\n', k1, theta_d1, theta_d1*180/pi);
fprintf('  Trajectory points: %d\n', size(trajectory1, 1));
fprintf('  Start position: [%.2f, %.2f, %.2f] [mm]\n', trajectory1(1,:));
fprintf('  End position: [%.2f, %.2f, %.2f] [mm]\n', trajectory1(end,:));

% Use a point from the trajectory as target and verify
if size(trajectory1, 1) > 1
    % Select a target point from the trajectory (e.g., middle point)
    mid_idx = round(size(trajectory1, 1) / 2);
    target_pos = trajectory1(mid_idx, 1:3); % Row vector [x, y, z]
    
    % Create initial needle pose (at start position)
    % Assume initial orientation: gamma=0, phi=0, theta=0
    initial_needle_pose = [trajectory1(1,1:3), 0, 0, 0];
    [P_tb1, T_tb] = Cal_Ptb1_Ttb(initial_needle_pose);
    
    % Calculate k and theta_d using original function
    theta_initial = 0; % initial rotation angle
    [k_calc, P_tt, theta_d_calc] = Cal_k_P_tt_theta_d(target_pos, T_tb, theta_initial);
    
    fprintf('  Target position: [%.2f, %.2f, %.2f] [mm]\n', target_pos);
    fprintf('  Calculated k: %.6f [1/mm] (expected: %.6f)\n', k_calc, k1);
    fprintf('  Calculated theta_d: %.4f [rad] (%.1f deg) (expected: %.4f rad, %.1f deg)\n', ...
        theta_d_calc, theta_d_calc*180/pi, theta_d1, theta_d1*180/pi);

    % Consistency note:
    % Depending on the sign convention, (k, theta_d) and (-k, theta_d + pi) can describe
    % the same physical trajectory. The forward function in this repo later uses abs(k).
    k_err_direct_pct = abs(k_calc - k1) / max(1e-12, abs(k1)) * 100;
    th_err_direct_deg = angleDiff(theta_d_calc, theta_d1) * 180/pi;

    k_equiv = -k_calc;
    th_equiv = wrapTo2Pi(theta_d_calc - pi);
    k_err_equiv_pct = abs(k_equiv - k1) / max(1e-12, abs(k1)) * 100;
    th_err_equiv_deg = angleDiff(th_equiv, theta_d1) * 180/pi;

    fprintf('  Direct errors:   k error = %.2f%%, theta_d error = %.2f deg\n', k_err_direct_pct, th_err_direct_deg);
    fprintf('  Equiv. errors:   k error = %.2f%%, theta_d error = %.2f deg  (compare k_equiv=-k_calc, theta_equiv=theta_d_calc-pi)\n', ...
        k_err_equiv_pct, th_err_equiv_deg);
end

% Test Case 2
fprintf('\nTest Case 2:\n');
fprintf('  Input: k = %.6f [1/mm], theta_d = %.4f [rad] (%.1f deg)\n', k2, theta_d2, theta_d2*180/pi);
fprintf('  Trajectory points: %d\n', size(trajectory2, 1));
fprintf('  Start position: [%.2f, %.2f, %.2f] [mm]\n', trajectory2(1,:));
fprintf('  End position: [%.2f, %.2f, %.2f] [mm]\n', trajectory2(end,:));

if size(trajectory2, 1) > 1
    mid_idx = round(size(trajectory2, 1) / 2);
    target_pos = trajectory2(mid_idx, 1:3); % Row vector [x, y, z]
    initial_needle_pose = [trajectory2(1,1:3), 0, 0, 0];
    [P_tb1, T_tb] = Cal_Ptb1_Ttb(initial_needle_pose);
    theta_initial = 0;
    [k_calc, P_tt, theta_d_calc] = Cal_k_P_tt_theta_d(target_pos, T_tb, theta_initial);
    
    fprintf('  Target position: [%.2f, %.2f, %.2f] [mm]\n', target_pos);
    fprintf('  Calculated k: %.6f [1/mm] (expected: %.6f)\n', k_calc, k2);
    fprintf('  Calculated theta_d: %.4f [rad] (%.1f deg) (expected: %.4f rad, %.1f deg)\n', ...
        theta_d_calc, theta_d_calc*180/pi, theta_d2, theta_d2*180/pi);

    k_err_direct_pct = abs(k_calc - k2) / max(1e-12, abs(k2)) * 100;
    th_err_direct_deg = angleDiff(theta_d_calc, theta_d2) * 180/pi;

    k_equiv = -k_calc;
    th_equiv = wrapTo2Pi(theta_d_calc - pi);
    k_err_equiv_pct = abs(k_equiv - k2) / max(1e-12, abs(k2)) * 100;
    th_err_equiv_deg = angleDiff(th_equiv, theta_d2) * 180/pi;

    fprintf('  Direct errors:   k error = %.2f%%, theta_d error = %.2f deg\n', k_err_direct_pct, th_err_direct_deg);
    fprintf('  Equiv. errors:   k error = %.2f%%, theta_d error = %.2f deg  (compare k_equiv=-k_calc, theta_equiv=theta_d_calc-pi)\n', ...
        k_err_equiv_pct, th_err_equiv_deg);
end

% Test Case 3
fprintf('\nTest Case 3:\n');
fprintf('  Input: k = %.6f [1/mm], theta_d = %.4f [rad] (%.1f deg)\n', k3, theta_d3, theta_d3*180/pi);
fprintf('  Trajectory points: %d\n', size(trajectory3, 1));
fprintf('  Start position: [%.2f, %.2f, %.2f] [mm]\n', trajectory3(1,:));
fprintf('  End position: [%.2f, %.2f, %.2f] [mm]\n', trajectory3(end,:));

if size(trajectory3, 1) > 1
    mid_idx = round(size(trajectory3, 1) / 2);
    target_pos = trajectory3(mid_idx, 1:3); % Row vector [x, y, z]
    initial_needle_pose = [trajectory3(1,1:3), 0, 0, 0];
    [P_tb1, T_tb] = Cal_Ptb1_Ttb(initial_needle_pose);
    theta_initial = 0;
    [k_calc, P_tt, theta_d_calc] = Cal_k_P_tt_theta_d(target_pos, T_tb, theta_initial);
    
    fprintf('  Target position: [%.2f, %.2f, %.2f] [mm]\n', target_pos);
    fprintf('  Calculated k: %.6f [1/mm] (expected: %.6f)\n', k_calc, k3);
    fprintf('  Calculated theta_d: %.4f [rad] (%.1f deg) (expected: %.4f rad, %.1f deg)\n', ...
        theta_d_calc, theta_d_calc*180/pi, theta_d3, theta_d3*180/pi);

    k_err_direct_pct = abs(k_calc - k3) / max(1e-12, abs(k3)) * 100;
    th_err_direct_deg = angleDiff(theta_d_calc, theta_d3) * 180/pi;

    k_equiv = -k_calc;
    th_equiv = wrapTo2Pi(theta_d_calc - pi);
    k_err_equiv_pct = abs(k_equiv - k3) / max(1e-12, abs(k3)) * 100;
    th_err_equiv_deg = angleDiff(th_equiv, theta_d3) * 180/pi;

    fprintf('  Direct errors:   k error = %.2f%%, theta_d error = %.2f deg\n', k_err_direct_pct, th_err_direct_deg);
    fprintf('  Equiv. errors:   k error = %.2f%%, theta_d error = %.2f deg  (compare k_equiv=-k_calc, theta_equiv=theta_d_calc-pi)\n', ...
        k_err_equiv_pct, th_err_equiv_deg);
end

fprintf('\n=== Test Complete ===\n');
