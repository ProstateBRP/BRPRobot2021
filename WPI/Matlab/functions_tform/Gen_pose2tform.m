function [Gab] = Gen_pose2tform(Pose_Vec)
% Gen_pose2tform
% 位置姿勢(x,y,z,Rx,Ry,Rz)から同時変換行列を生成
    Rz = Pose_Vec(6);
    Ry = Pose_Vec(5);
    Rx = Pose_Vec(4);
    Gab = eul2tform([Rz, Ry, Rx],'ZYX'); % オイラー角から同時変換行列生成（Matlab関数）
    Gab(1:3,4) = Pose_Vec(1:3);            % 同時変換行列に並進位置を格納

end

