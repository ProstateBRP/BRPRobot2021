function [Needle_pose_sensor] = Imitation_Sensor(Needle_pose)
% IMITATION_SENSOR ニードルの位置を取得するセンサを模擬
% input：
%   Needle_pose - ニードルの位置姿勢([x,y,z,gamma,phi,theta])
% output：
%   Needle_pose_sensor - センサ誤差を含んだニードルの位置姿勢

% センサ模擬(現在は、値を直接代入)
x     = Needle_pose(1) * 1 + 0; %[mm]
y     = Needle_pose(2) * 1 + 0; %[mm]
z     = Needle_pose(3) * 1 + 0; %[mm]
gamma = Needle_pose(4) * 1 + 0; %[rad]
phi   = Needle_pose(5) * 1 + 0; %[rad]
theta = Needle_pose(6) * 1 + 0; %[rad]

Needle_pose_sensor = [x,y,z,gamma,phi,theta];

end

