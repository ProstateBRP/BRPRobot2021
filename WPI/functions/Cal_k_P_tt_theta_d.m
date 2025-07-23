function [k, P_tt, theta_d] = Cal_k_P_tt_theta_d(Target_Pos, T_tb, theta)
% Cal_k_P_tt_theta_d  論文の計算式に基づいた計算を実施
% input：
%   Target_Pos - 目標位置[mm]
%   T_tb       - the transformation from the robot base to the needle tip
% output：
%   k       - the desired vurvature 
%   P_tt    - 
%   theta_d - target angle[rad]

% 論文式(3)
P_tb2 = [Target_Pos';1]; % base→targetのポジション
P_tt = T_tb \ P_tb2; % 同次変換行列との計算のため、末尾に1を追加している。

% 論文式(4)
theta_d_dash = atan2(-P_tt(1),P_tt(2)) + pi; % Matlabはatan2(Y,X)だが、計算するのはy軸の負とx-y平面上の投影目標位置とのなす角度なので、
                                            % P_tt(2)(y軸要素の負)をXに代入し、piを加算している。                                 

% 論文式(5)
if (theta + theta_d_dash) >= 2*pi
    theta_d = theta + theta_d_dash - 2*pi;
else
    theta_d = theta + theta_d_dash;
end

% 論文式(6)
Rz = Cal_Rotation_Matrix(theta_d_dash, R_axis.z); % z軸周りの回転行列
Rz = [[Rz,[0;0;0]];0,0,0,1]; %T_tbは4x4、Rzは3x3行列。今回はRzを無理やり4x4行列ｎしてみる。
T_tb2 = eye(4);
T_tb2(1:3,4) = P_tb2(1:3,1);
T_tt_dash = (T_tb * Rz) \ T_tb2;                   % この式について納得したものの、引き続き注意（さとし、村上で議論 20250104。Farid, Liの論文を見比べた。村上が特に気になるのはRzをかける順番）
P_tt_dash = T_tt_dash(1:3,4); 
% P_tt_dash = cross(inv(cross(T_tb,Rz)),P_tb2);                   % ここは外積計算なの？


% 論文式(7)
Radius = P_tt_dash(2)/2 + (P_tt_dash(3)^2)/(2*P_tt_dash(2)); % ←これ合ってる？x軸は使わなくていい？というかどういう計算？

% 論文式(8)
k = 1/Radius;

end

