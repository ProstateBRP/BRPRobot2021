clc;
clear;

delete_all;

%Initialzation and setup for parameters
server = Server('open_loop', true, 'simulation', false, 'exsi',false);
% Must determine control type!
%Robot setup and bring up
server.Run();