%% Create GalilTools COM server object
g = init_galil();

%% Control Module Initialization
% Access Relay for Inner & Outer
g.command('SB 3');
pause(0.1);
disp('Relay for drivers should be turned on');


%% Needle Steering
% Set constant insertion speed
insertion_speed = 3; % Voltage
g.command(['OFA=', num2str(insertion_speed)]);
disp(['Set Inner Motor Speed to: ', num2str(insertion_speed), ' V']);


% Insert needle
% TODO: Confirm motor direction with the needle insertion direction on the robot.
g.command('SB 5'); 
pause(1);


% % Set RPM using constant voltage
% motor_num = 6;
% direction = 0;
% voltage = 3;
% set_vel_volt(g, motor_num, direction, voltage);
% 
% pause(5);
% 
% % Set desired RPM using PID controller
% motor_num = 6;
% direction = 0;
% desired_rpm = 60;
% max_error = 5;
% set_rpm_pid(g, motor_num, direction, desired_rpm, max_error)
% 
% pause(5);

% Retract needle
g.command('CB 5');
% pause(0.5);
% g.command('SB 4');


%% Terminate Backend Program
disable_galil(g)  

close all;
clearvars;

disp('Program terminated successfully');
