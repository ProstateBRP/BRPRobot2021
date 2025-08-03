


angle_eul = [pi, -pi/2, -pi/4]



% P_tb1  = [Needle_pose(1:3),1]'; % 同次変換行列との計算のため、末尾に1を追加している。
gamma = angle_eul(1); %[rad]
phi   = angle_eul(2); %[rad]
theta = angle_eul(3); %[rad]

% 回転行列生成（論文式(9)）
Rx = Cal_Rotation_Matrix(gamma,R_axis.x);
Ry = Cal_Rotation_Matrix(phi  ,R_axis.y);
Rz = Cal_Rotation_Matrix(theta,R_axis.z);
R_tb = Rz * Ry * Rx

%%
% Coinのz軸方向を取得
z_direction_Coin = euler2z(angle_eul);

% ローカルz軸（絶対固定）
zHat = euler2z(Needle_euler_init);
zHat = zHat / norm(zHat);  % 正規化

% y軸はCoinのz軸方向を基に、zHatと最短で直交するよう調整
yHat_temp = z_direction_Coin / norm(z_direction_Coin);
yHat = yHat_temp - (dot(yHat_temp, zHat) * zHat); % zHatとの直交成分を抽出
yHat = yHat / norm(yHat);

% x軸はy軸とz軸の外積で計算
xHat = cross(yHat, zHat);
xHat = xHat / norm(xHat);