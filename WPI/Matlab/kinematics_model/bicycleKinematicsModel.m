function [gab, nb] = bicycleKinematicsModel(gab0, du1, du2, V1, V2, l2, e3)
% 
% function [gab, nb, i] = BMRun(gab0, nb, i, du1, du2, time)
%   gab0 = Initial Frame B to Frame A transformation
%   du1 = Needle insertion distance displacement amount for this iteration
%   du2 = Needle rotational angle displacement amount for this iteration 

% Access configuration parameters
%Solve kinematics for this iteration
if du1 == 0 && du2 == 0
    gab = gab0;
    nb = (gab0(1:3,1:3) * l2 * e3) + gab0(1:3,4);
    return;
end
gab = gab0 * expSE3(toLieSE3((du1 * V1) + (du2 * V2)));
nb = (gab0(1:3,1:3) * l2 * e3) + gab0(1:3,4); % gab0で計算してるけど、gabで計算すべきじゃない？

