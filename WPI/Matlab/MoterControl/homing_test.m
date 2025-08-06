clear;
close all;



%% Create GalilTools COM server object
g = init_galil();

%% Set A, B Port as Servo
response = g.command('MT 1,1');
response = g.command('KP 0,0');
response = g.command('KI 0,0');
response = g.command('KD 0,0');
response = g.command('SH A');

% response = g.command('MT 1');
% response = g.command('KP 0');
% response = g.command('KI 0');
% response = g.command('KD 0');
response = g.command('SH B');

% response = g.command('OFB=3');

% Turn off DO1 and DO2 (Safety feature)
response = g.command('CB 1');
response = g.command('CB 2');
response = g.command('CB 3');
response = g.command('CB 4');
response = g.command('CB 5');

%% Control Module Initialization
% Access Relay
g.command('SB 3');
pause(0.1);
disp('Relay for drivers should be turned on');

%% Record encoder tick at home
% home_pos = record_home_pos(g)
home_pos = 0;

%% Insert2;
direction = 1;
voltage = 2;
pause
disp("Insertion ongoing")
move_insertion(g, direction, voltage);

pause
stop_pos = record_home_pos(g)
disp("Stopped")
stop_insertion(g, direction);



%% Homing
threshold = 1000;
home_insertion(g, home_pos, threshold);
% % % record_home_pos(g)% 
disable_galil(g);

