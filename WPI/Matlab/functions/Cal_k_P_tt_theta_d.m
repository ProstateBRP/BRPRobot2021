function [k, P_tt, theta_d] = Cal_k_P_tt_theta_d(Target_Pos, T_tb, theta)
% Cal_k_P_tt_theta_d  Perform calculation based on the paper's formulas
% input:
%   Target_Pos - target position [mm]
%   T_tb       - the transformation from the robot base to the needle tip
% output:
%   k       - the desired curvature
%   P_tt    -
%   theta_d - target angle [rad]

% Paper equation (3)
P_tb2 = [Target_Pos';1]; % position from base to target
P_tt = T_tb \ P_tb2; % Append 1 at the end for homogeneous transformation matrix calculation.

% Paper equation (4)
theta_d_dash = atan2(-P_tt(1),P_tt(2)) + pi; % MATLAB uses atan2(Y,X); we compute the angle between the negative y-axis and the projection of the target on the x-y plane,
                                            % so -P_tt(1) and P_tt(2) are used and pi is added.

% Paper equation (5)
if (theta + theta_d_dash) >= 2*pi
    theta_d = theta + theta_d_dash - 2*pi;
else
    theta_d = theta + theta_d_dash;
end

% Paper equation (6)
Rz = Cal_Rotation_Matrix(theta_d_dash, R_axis.z); % rotation matrix about z-axis
Rz = [[Rz,[0;0;0]];0,0,0,1]; % T_tb is 4x4 and Rz is 3x3; here Rz is extended to 4x4.
T_tb2 = eye(4);
T_tb2(1:3,4) = P_tb2(1:3,1);
T_tt_dash = (T_tb * Rz) \ T_tb2;                   % Note: formula agreed but still under review (Satoshi, Murakami 20250104; compared Farid and Li papers; order of applying Rz is of concern).
P_tt_dash = T_tt_dash(1:3,4); 
% P_tt_dash = cross(inv(cross(T_tb,Rz)),P_tb2);   % Is this cross product calculation?


% Paper equation (7)
Radius = P_tt_dash(2)/2 + (P_tt_dash(3)^2)/(2*P_tt_dash(2)); % Verify: is this correct? Is x-axis unused? What does this formula represent?

% Paper equation (8)
k = 1/Radius;

end

