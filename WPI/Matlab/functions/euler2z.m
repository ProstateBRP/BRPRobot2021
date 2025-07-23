%% オイラー角からz軸方向を計算する補助関数
function zVec = euler2z(euler)
    yaw = euler(3);   % Z軸周りの回転
    pitch = euler(2); % Y軸周りの回転
    roll = euler(1);  % X軸周りの回転

    % 回転行列を計算 (ZYX順)
    Rz = [cos(yaw), -sin(yaw), 0;
          sin(yaw),  cos(yaw), 0;
               0,          0, 1];
    Ry = [ cos(pitch), 0, sin(pitch);
                 0, 1,        0;
          -sin(pitch), 0, cos(pitch)];
    Rx = [1,       0,        0;
          0,  cos(roll), -sin(roll);
          0,  sin(roll),  cos(roll)];

    % 合成回転行列 (ZYX順)
    R = Rz * Ry * Rx;

    % z軸方向を抽出
    zVec = R(:, 3);
end
