clc;
clear;

%Initialzation and setup for parameters
server = Server('open_loop', true, 'simulation', false);
server.connect();
% Must determine control type!
%Robot setup and bring up
server.Run();