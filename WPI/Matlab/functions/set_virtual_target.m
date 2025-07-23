function [pos_virtual_target, xHat, yHat, zHat] = set_virtual_target(Needle_init, Coin_init, Target_local,xHat, yHat, zHat)

Needle_euler_init = [Needle_init(4), Needle_init(5), Needle_init(6)];
Needle_pos_init = [Needle_init(1), Needle_init(2), Needle_init(3)]; % [mm]

Coin_euler_init = [Coin_init(4), Coin_init(5), Coin_init(6)];

% Coinのz軸方向を取得
z_direction_Coin = euler2z(Coin_euler_init);

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

%% ---(2) 同時変換行列の作成)---
T_local_to_global = eye(4);
T_local_to_global(1:3, 1:3) = [xHat, yHat, zHat]; % 回転部分
T_local_to_global(1:3, 4) = Needle_pos_init;     % 平行移動部分

%% ---(3) ターゲットのローカル座標をグローバル座標に変換)---
Target_local_homogeneous = [Target_local'; 1];  % ローカル座標でのターゲット位置 (同次座標系)
Target_global_homogeneous = T_local_to_global * Target_local_homogeneous; % グローバル座標でのターゲット位置 (同次座標系)
Target_global = Target_global_homogeneous(1:3); % 3次元座標

%% ---(4) プロット)---

figure; % Original
% figure(1); % test
% clf; % test

% グローバル座標系の原点
% plot3(0, 0, 0, 'ko', 'MarkerSize', 10, 'DisplayName', 'Global Origin');


% ニードルの初期位置
plot3(Needle_pos_init(1), Needle_pos_init(2), Needle_pos_init(3), 'ro', 'MarkerSize', 10, 'DisplayName', 'Needle Origin');
hold on;
% ローカル座標系の軸
quiver3(Needle_pos_init(1), Needle_pos_init(2), Needle_pos_init(3), ...
    xHat(1), xHat(2), xHat(3), 50, 'r', 'LineWidth', 1.5, 'DisplayName', 'Local X');
quiver3(Needle_pos_init(1), Needle_pos_init(2), Needle_pos_init(3), ...
    yHat(1), yHat(2), yHat(3), 50, 'g', 'LineWidth', 1.5, 'DisplayName', 'Local Y');
quiver3(Needle_pos_init(1), Needle_pos_init(2), Needle_pos_init(3), ...
    zHat(1), zHat(2), zHat(3), 50, 'b', 'LineWidth', 1.5, 'DisplayName', 'Local Z');

% ターゲット位置
plot3(Target_global(1), Target_global(2), Target_global(3), 'ms', 'MarkerSize', 10, 'DisplayName', 'Target Global');

% z_direction_Coin の可視化
quiver3(Needle_pos_init(1), Needle_pos_init(2), Needle_pos_init(3), ...
    z_direction_Coin(1), z_direction_Coin(2), z_direction_Coin(3), 50, 'k--', 'LineWidth', 1.5, 'DisplayName', 'z direction Coin');

legend;
title('Local and Global Coordinate Visualization with Adjusted Axes');

grid on;
axis equal;
xlabel('X [mm]');
ylabel('Y [mm]');
zlabel('Z [mm]');

pos_virtual_target = Target_global';

end

