function [rot_dir,theta0] = Update_rot_dir(theta, theta0, rot_dir)
% CAL_ROT_DIR 回転方向を更新する
% input：
%   theta - needle's rotation angle
% output：
%   rot_dir - needle's rotation direction (0:CW, 1:CCW)

theta_diff = theta - theta0;
theta0 = theta;
if (theta > 2*pi) && (rot_dir == CW_dir.CW)
    rot_dir = CW_dir.CCW; % 回転角360deg超過で、回転方向をCW→CCWに更新
elseif (theta < 0) && (rot_dir == CW_dir.CCW)
    rot_dir = CW_dir.CW; % 回転角0deg未満で、回転方向をCCW→CWに更新

% elseif (theta_diff < 0) && (rot_dir == CW_dir.CW)
%     rot_dir = CW_dir.CCW;  % CWなのにthetaが減少した場合、ジャンプ判定として回転方向をCW→CCWに更新
%     theta0 = theta + 2*pi; % 次の演算でジャンプ判定にならないようにtheta0を補正
% elseif (theta_diff > 0) && (rot_dir == CW_dir.CCW)
%     rot_dir = CW_dir.CW;  % CCWなのにthetaが増加した場合、ジャンプ判定として回転方向をCCW→CWに更新
%     theta0 = theta - 2*pi; % 次の演算でジャンプ判定にならないようにtheta0を補正
% elseif abs(theta_diff) > 2*pi
%     if theta_diff > 0
%         theta0 = theta0 - 2*pi;
%     else
%         theta0 = theta0 + 2*pi;
%     end

end

% rot_dir = CW_dir.CW; % 臨時（バグが取れたら削除）

end

