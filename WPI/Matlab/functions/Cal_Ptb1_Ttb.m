function [P_tb1, T_tb] = Cal_Ptb1_Ttb(Needle_pose)
% CAL_PTB1_TTB ニードル位置情報から位置ベクトル及び同時変換行列を生成する
% input：
%   Needle_pose - ニードルの位置姿勢([x,y,z,gamma,phi,theta])
% output：
%   P_tb1：the target position vector defined in the robot base frame
%   T_tb：the transformation from the robot base to the needle tip

    % Needle_poseを分割
    P_tb1  = [Needle_pose(1:3),1]'; % 同次変換行列との計算のため、末尾に1を追加している。
    gamma = Needle_pose(4); %[rad]
    phi   = Needle_pose(5); %[rad]
    theta = Needle_pose(6); %[rad]
    
    % 回転行列生成（論文式(9)）
    Rx = Cal_Rotation_Matrix(gamma,R_axis.x);
    Ry = Cal_Rotation_Matrix(phi  ,R_axis.y);
    Rz = Cal_Rotation_Matrix(theta,R_axis.z);
    R_tb = Rz * Ry * Rx;
    
    % 同次変換行列生成（論文式(10)）
    T_tb = [[R_tb;0,0,0],P_tb1]; % P_tb1はbase→tipを指す。P_tb2はbase→targetを指す。

end

