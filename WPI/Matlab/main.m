clc;
clear;

%Initialzation and setup for parameters
server = Server('open_loop', true, 'simulation', true,'host','130.215.192.215');
server.connect();
% Must determine control type!
%Robot setup and bring up
server.Run();