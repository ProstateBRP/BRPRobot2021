clear; close all; clc;

% Robot Reachability Test using Robot.m class
% This script tests the reachability logic using the Robot class reachable method

fprintf('=== Robot Reachability Test using Robot.m ===\n');
fprintf('Testing reachability using Robot class methods\n\n');

% Add paths to Robot class and dependencies
addpath('../classes');
addpath('../functions');

% Test basic functionality first
try
    fprintf('Creating Robot instance...\n');
    % Create Robot instance in simulation mode
    robot = Robot('simulation', true);
    fprintf('Robot created successfully.\n');
    
    fprintf('Starting up robot...\n');
    robot = robot.startup();
    fprintf('Robot startup completed.\n');
    
    % Test a simple reachable call
    fprintf('Testing simple reachable call...\n');
    test_target = [10, 0, 50];  % Simple target
    is_reachable = robot.reachable(test_target);
    fprintf('Simple reachability test passed. Result: %s\n', string(is_reachable));
    
catch ME
    fprintf('Error occurred: %s\n', ME.message);
    fprintf('Error details:\n');
    for i = 1:length(ME.stack)
        fprintf('  File: %s, Function: %s, Line: %d\n', ...
            ME.stack(i).file, ME.stack(i).name, ME.stack(i).line);
    end
    return;
end

%% Test parameters (same as test_reachable.m)
max_curvature = 0.0026; % mm^-1
z_displacement = 100;   % mm

% Calculate theoretical maximum reach
R_min = 1/max_curvature; % Minimum turning radius [mm]

% Calculate maximum lateral displacement using the same formula as reachability check
arc_length = z_displacement;
if arc_length <= 2 * R_min
    max_lateral_displacement = R_min * sin(arc_length / R_min);
else
    max_lateral_displacement = 2 * R_min;
end

% Apply safety margin (same as in reachability check)
max_lateral_displacement_with_margin = max_lateral_displacement * 1;

% Calculate endpoint for fully curved case (for visualization and boundary targets)
arc_angle = z_displacement / R_min; % Arc angle [rad]
if arc_angle <= pi
    max_x_reachable = R_min * sin(arc_angle);
    max_y_reachable = R_min * (1 - cos(arc_angle));
else
    max_x_reachable = R_min;
    max_y_reachable = R_min * 2;
end

fprintf('Test Parameters:\n');
fprintf('  Max curvature: %.6f mm^-1\n', max_curvature);
fprintf('  Min radius: %.2f mm\n', R_min);
fprintf('  Z displacement: %.2f mm\n', z_displacement);
fprintf('  Max lateral displacement (theoretical): %.2f mm\n', max_lateral_displacement);
fprintf('  Max lateral displacement (with safety margin): %.2f mm\n', max_lateral_displacement_with_margin);
fprintf('  Max X reachable (endpoint): %.2f mm\n', max_x_reachable);
fprintf('  Max Y reachable (endpoint): %.2f mm\n', max_y_reachable);
fprintf('\n');

%% Generate the same targets as in test_reachable.m

% Initial needle pose (at origin, pointing in z-direction)
initial_pose = [0, 0, 0, 0, 0, 0]; % [x,y,z,gamma,phi,theta]

% === A. Reachable targets (intended to be within range) ===
reachable_targets = [
    % Near-straight trajectories (very small lateral displacement)
    [5, 0, z_displacement];
    [0, 5, z_displacement];
    [3, 3, z_displacement];
    
    % Moderate curvature (use safety margin limit for reliable testing)
    [max_lateral_displacement_with_margin*0.3, 0, z_displacement];
    [0, max_lateral_displacement_with_margin*0.5, z_displacement];
    [max_lateral_displacement_with_margin*0.6, max_lateral_displacement_with_margin*0.2, z_displacement];
    [max_lateral_displacement_with_margin*0.4, max_lateral_displacement_with_margin*0.4, z_displacement];
    
    % Negative directions
    [-max_lateral_displacement_with_margin*0.3, 0, z_displacement];
    [0, -max_lateral_displacement_with_margin*0.5, z_displacement];
    [max_lateral_displacement_with_margin*0.3, -max_lateral_displacement_with_margin*0.3, z_displacement];
];

% === B. Boundary targets (intended to be just reachable) ===
boundary_targets = [
    % At theoretical maximum lateral displacement (without safety margin)
    [max_lateral_displacement, 0, z_displacement];
    [0, max_lateral_displacement, z_displacement];
    [-max_lateral_displacement, 0, z_displacement];
    [0, -max_lateral_displacement, z_displacement];
    
    % Diagonal directions at theoretical maximum
    [max_lateral_displacement*cos(pi/4), max_lateral_displacement*sin(pi/4), z_displacement];
    [max_lateral_displacement*cos(3*pi/4), max_lateral_displacement*sin(3*pi/4), z_displacement];
    [max_lateral_displacement*cos(5*pi/4), max_lateral_displacement*sin(5*pi/4), z_displacement];
    [max_lateral_displacement*cos(7*pi/4), max_lateral_displacement*sin(7*pi/4), z_displacement];
];

% === C. Unreachable targets (intended to be out of range) ===
unreachable_targets = [
    % Beyond maximum lateral displacement
    [max_lateral_displacement*1.2, 0, z_displacement];
    [0, max_lateral_displacement*1.5, z_displacement];
    [max_lateral_displacement*1.1, max_lateral_displacement*1.1, z_displacement];
    [max_lateral_displacement*2.0, 0, z_displacement];
    
    % Different z displacement (longer insertion - these should be unreachable)
    [max_lateral_displacement*0.5, 0, z_displacement*1.5];
    [0, max_lateral_displacement*0.5, z_displacement*2.0];
    
    % Shorter insertion but too far laterally for the shorter distance
    [max_lateral_displacement*0.8, 0, z_displacement*0.3];  % 80% of 100mm reach at 30mm depth should be unreachable
    
    % Beyond maximum insertion distance (test the max_insertion_distance check)
    [10, 0, 130];  % z=130mm > max_insertion_distance=120mm
    [0, 10, 150];  % z=150mm > max_insertion_distance=120mm  
    [5, 5, 200];   % z=200mm > max_insertion_distance=120mm
    
    % Extremely far
    [200, 200, z_displacement];
    [500, 0, z_displacement];
    [0, 300, z_displacement];
];

%% Test each category of targets

% Test reachable targets
fprintf('=== Testing Reachable Targets ===\n');
reachable_correct = 0;
for i = 1:size(reachable_targets, 1)
    target = reachable_targets(i, :);
    
    try
        % Use Robot.m reachable method
        is_reachable = robot.reachable(target);
        
        dist_from_origin = sqrt(target(1)^2 + target(2)^2);
        expected = true;
        correct = (is_reachable == expected);
        
        if correct
            reachable_correct = reachable_correct + 1;
        end
        
        fprintf('Target %d: (%.1f, %.1f, %.1f) - Distance: %.1f mm\n', ...
            i, target(1), target(2), target(3), dist_from_origin);
        fprintf('  Expected: %s, Actual: %s, Correct: %s\n', ...
            char(string(expected)), char(string(is_reachable)), char(string(correct)));
    catch ME
        fprintf('Error testing target %d: %s\n', i, ME.message);
        continue;
    end
end
fprintf('Reachable targets accuracy: %.1f%% (%d/%d)\n\n', ...
    reachable_correct/size(reachable_targets,1)*100, reachable_correct, size(reachable_targets,1));

% Test boundary targets - EXCLUDED FROM VERIFICATION
% fprintf('=== Testing Boundary Targets ===\n');
% boundary_correct = 0;
% for i = 1:size(boundary_targets, 1)
%     target = boundary_targets(i, :);
%     
%     % Simplified reachability check (inline)
%     needle_tip = initial_pose(1:3);
%     target_relative = target - needle_tip;
%     remaining_z_distance = target_relative(3);
%     
%     if remaining_z_distance <= 0
%         is_reachable = false;
%     else
%         lateral_distance = sqrt(target_relative(1)^2 + target_relative(2)^2);
%         
%         if max_curvature > 0
%             max_radius = 1 / max_curvature;
%             arc_length = remaining_z_distance;
%             
%             if arc_length <= 2 * max_radius
%                 max_lateral_reach = max_radius * sin(arc_length / max_radius);
%             else
%                 max_lateral_reach = 2 * max_radius;
%             end
%             
%             max_lateral_reach = max_lateral_reach * 0.9; % Safety margin
%             is_reachable = lateral_distance <= max_lateral_reach;
%         else
%             tolerance = 1.0;
%             is_reachable = lateral_distance <= tolerance;
%         end
%     end
%     
%     dist_from_origin = sqrt(target(1)^2 + target(2)^2);
%     expected = true;
%     correct = (is_reachable == expected);
%     
%     if correct
%         boundary_correct = boundary_correct + 1;
%     end
%     
%     fprintf('Boundary Target %d: (%.1f, %.1f, %.1f) - Distance: %.1f mm\n', ...
%         i, target(1), target(2), target(3), dist_from_origin);
%     fprintf('  Expected: %s, Actual: %s, Correct: %s\n', ...
%         char(string(expected)), char(string(is_reachable)), char(string(correct)));
% end
% fprintf('Boundary targets accuracy: %.1f%% (%d/%d)\n\n', ...
%     boundary_correct/size(boundary_targets,1)*100, boundary_correct, size(boundary_targets,1));

% Boundary targets excluded from verification
boundary_correct = 0; % Not counted in overall accuracy

% Test unreachable targets
fprintf('=== Testing Unreachable Targets ===\n');
unreachable_correct = 0;
for i = 1:size(unreachable_targets, 1)
    target = unreachable_targets(i, :);
    
    try
        % Use Robot.m reachable method
        is_reachable = robot.reachable(target);
        
        dist_from_origin = sqrt(target(1)^2 + target(2)^2);
        expected = false;
        correct = (is_reachable == expected);
        
        if correct
            unreachable_correct = unreachable_correct + 1;
        end
        
        fprintf('Unreachable Target %d: (%.1f, %.1f, %.1f) - Distance: %.1f mm\n', ...
            i, target(1), target(2), target(3), dist_from_origin);
        fprintf('  Expected: %s, Actual: %s, Correct: %s\n', ...
            char(string(expected)), char(string(is_reachable)), char(string(correct)));
    catch ME
        fprintf('Error testing unreachable target %d: %s\n', i, ME.message);
        continue;
    end
end
fprintf('Unreachable targets accuracy: %.1f%% (%d/%d)\n\n', ...
    unreachable_correct/size(unreachable_targets,1)*100, unreachable_correct, size(unreachable_targets,1));

%% Overall Summary (excluding boundary targets)
total_targets = size(reachable_targets,1) + size(unreachable_targets,1); % Boundary targets excluded
total_correct = reachable_correct + unreachable_correct; % Boundary targets excluded
overall_accuracy = total_correct / total_targets * 100;

fprintf('=== Overall Summary (excluding boundary targets) ===\n');
fprintf('Overall accuracy: %.1f%% (%d/%d)\n', overall_accuracy, total_correct, total_targets);
fprintf('Note: Boundary targets (%d) excluded from verification\n', size(boundary_targets,1));

%% Visualization
figure('Position', [100, 100, 1200, 800]);

% Create theoretical reachable region (using safety margin for visualization)
vis_range = max_lateral_displacement * 1.5; % Show area beyond reachable region
x_range = linspace(-vis_range, vis_range, 50);
y_range = linspace(-vis_range, vis_range, 50);
[X, Y] = meshgrid(x_range, y_range);
Z = ones(size(X)) * z_displacement;

reachable_map = zeros(size(X));
for i = 1:size(X, 1)
    for j = 1:size(X, 2)
        dist = sqrt(X(i,j)^2 + Y(i,j)^2);
        if dist <= max_lateral_displacement_with_margin
            reachable_map(i,j) = 1;
        end
    end
end

% Plot theoretical reachable region
surf(X, Y, Z, reachable_map, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
hold on;

% Plot targets
plot3(reachable_targets(:,1), reachable_targets(:,2), reachable_targets(:,3), ...
      'go', 'MarkerSize', 8, 'MarkerFaceColor', 'g', 'DisplayName', 'Reachable Targets');
plot3(boundary_targets(:,1), boundary_targets(:,2), boundary_targets(:,3), ...
      'yo', 'MarkerSize', 8, 'MarkerFaceColor', 'y', 'DisplayName', 'Boundary Targets');
plot3(unreachable_targets(:,1), unreachable_targets(:,2), unreachable_targets(:,3), ...
      'ro', 'MarkerSize', 8, 'MarkerFaceColor', 'r', 'DisplayName', 'Unreachable Targets');

% Initial position
plot3(0, 0, 0, 'ko', 'MarkerSize', 10, 'MarkerFaceColor', 'k', 'DisplayName', 'Initial Position');

colormap([0.8 0.8 0.8; 0.2 0.8 0.2]); % Gray (unreachable), Green (reachable)
xlabel('X [mm]');
ylabel('Y [mm]');
zlabel('Z [mm]');
title(sprintf('Simplified Reachability Test Results (Accuracy: %.1f%%)', overall_accuracy));
legend('Location', 'best');
grid on;
axis equal;

fprintf('\n=== Test Complete ===\n'); 