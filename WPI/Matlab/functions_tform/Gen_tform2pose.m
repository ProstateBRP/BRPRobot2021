function Pose_Vec = Gen_tform2pose(tform)
% Gen_tform2pose
% 同時変換行列から位置姿勢(x,y,z,Rx,Ry,Rz)を生成

% Rnew = Gab(1:3,1:3);
% eul_new = rotm2eul(Rnew,'ZYX');
eul_new = tform2eul(tform,'ZYX');
% eul_new = mod(eul_new + 2*pi, 2*pi); % -pi~piから0~2piの範囲に変換
Rx = eul_new(3);
Ry = eul_new(2);
Rz = eul_new(1); % [rad]

% 更新後のニードル位置姿勢をまとめる
Pose_Vec = [tform(1:3,4)', Rx, Ry, Rz];
end

