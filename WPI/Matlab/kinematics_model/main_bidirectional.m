% This script is used to simulate closed-loop needle insertion using
% the CURV and image feedback
clear; clc; close all;
% Add path
addpath(genpath("../"))
simulation_configurations_curv_steering;
bicycle_model_configurations;

%% Initialization
% Initial conditions:
needle_tip_position = zeros(3,1,1);
needle_tip_position(:,:,1) = [0;0;0];
% Initial coordinate frame
Gab = zeros(4,4,1);
Gab(4,4,:) = 1;
% Initial pitch angle
beta = 0;
Gab(:,:,1) = [1 0 0 0;...
    0 cosd(beta) -sind(beta) 0;...
    0 sind(beta) cosd(beta) 0;...
    0 0 0 1];
% The position of the origin of the transform Gab in each iteration
frame_position = zeros(3, 1, 1);
frame_position(1:3,1) =  Gab(1:3,4,1)';
% Assuming the actual needle position as seen in the imager is equal to the
% kinematic model
actual_needle_pos = Gab(1:3,4,1);
weight = 10; % Linear regression weight for the last and first data point
%% Configuration for tip axis visualization
triad('scale', 3, 'linewidth', 2.5);
hold on
rgb_axes = triad('Scale', 10, 'linewidth', 2.5);
grid minor
xlabel('x(mm)')
ylabel('y(mm)')
zlabel('z(mm)')
title('simulated trajectory')

%% CURV parameters
% Robot configs
target_pt = [0,0,100,1];
old_target = target_pt;
s = target_pt(3); % Total insertion length (mm)
w_max = 4 * pi/1; % Max rotational velocity (rad/s)
rotation_speed(1) = w_max; % Used for plotting purposes (rad/s)
c = 60; % Gaussian width (SD) (°)
theta(1) = 0; % Initial needle rotation angle (°)
u1 = 1; % insertion speed (mm/s)
% alpha = 0;
alpha = 0.5;
theta_d = 0;
direction = 'cw';
%% Simulation Configs
i = 1;
animation_flag = false;
animation_res= 100;
flag = false;

while frame_position(3,1,i) <= target_pt(3)

    disp(['z: ',num2str(frame_position(3,1,i))]);

    % Update CURV Each time we recieve a tip position update from the imager
    %{
    if flag == false && i~=1 && rem(time(i), feedback_freq) == 0
        % flag = true;
        % We receive a feedback from the imager
        actual_needle_pos(:,end+1) = image_feedback(Gab(1:3,4,i), 'high', 'const');
        target_pt = target_feedback(target_pt,'high','rand');
        % Replace the kinematic estimation with the corrected estimation
        Gab(:,:,i) = calc_needle_pose(actual_needle_pos,weight,theta(i));
        [theta_d, alpha] = update_curv_params(Gab(:,:,i), target_pt, max_curvature, theta(i));
        scatter3(Gab(1,4,i),Gab(2,4,i),Gab(3,4,i ))
    end
    %}

    [u2,direction] = bidirectional_curv_steering(alpha,c,w_max,theta_d,theta(i),direction);
    rotation_speed(i+1) = u2; % For plotting purposes
    theta(i+1) = theta(i) + (sim_time * u2);

    du1 = sim_time * u1;
    du2 = sim_time * u2;

    % Calculating the kinematics using nonholonomic bicycle model
    [Gab(:,:,i+1), needle_tip_position(:,:,i)] = bicycleKinematicsModel(Gab(:,:,i), ...
        du1, du2, V1,V2,l2, e3);
    frame_position(:,:,i+1) = Gab(1:3,4,i+1);
    
    %Plot Trajectory
    show_animation(i,animation_res,target_pt,old_target, frame_position,Gab,rgb_axes, animation_flag);
    old_target = target_pt;
    i=i+1;
end

flag = false;
plot_results(theta,rotation_speed,time,needle_tip_position,frame_position, flag);
% Print the difference
target_pt
frame_position(:,1,end)'

%% Data save
% save(['alpha_',num2str(alpha),'.mat'])
