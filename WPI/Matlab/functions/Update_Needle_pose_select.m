function [Needle_pose_new, Mom_Vec_tb] = Update_Needle_pose_select(omega, Stabbing_Vel, Time_resolution, Needle_pose,scale_model,disturbance)
% UPDATE_NEEDLE_POSE ニードル位置姿勢を更新
% input：
%   omega           - rotational velocity of the needle about its main axis[deg/sec?]
%   Stabbing_Vel    - ニードル刺入速度[mm/sec]
%   Time_resolution - 時間分解能[sec]
%   Needle_pose     - ニードル位置姿勢(x,y,z,gamma,phi,theta)
%   scale_model     - モデル誤差表現のためのスカラー（ニードルの曲がり具合）※デフォルト: 1
%   disturbance     - 外乱要素配列（x, y, z）※体内の構造物からの力など
% output：
%   Needle_pose_new - 更新後のNeedle_pose
%   Mom_Vec_tb      - ニードルの進行ベクトル(空間座標)

% 変更履歴
% 2024-08-16 - ニードルの刺入量計算に関するコメント追加（Adebar, Okamura, 2014IROS参照）（村上）

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

max_curvature = 0.001972715714235 * scale_model; %9.0402e-04

% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %%% 自作の幾何学運動模擬 %%%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 
% % ニードルの回転量を計算
% theta_delta = omega * Time_resolution; % [rad]
% 
% % ニードルの刺入量を計算(ニードル先端慣性座標基準)
% Stabbing_Momentum = Stabbing_Vel * Time_resolution; % [mm] *単位を村上追加 2024/08/16
% 
% % bend_scale = 0.5; % 曲がり具合を決める要素（マニュアル調整） [deg/mm] *村上追加 2024/08/16
% % kappa = bend_scale * pi/180 * scale_model; % 曲率 [rad/mm] *村上追加 2024/08/16
% kappa = max_curvature;
% rho = 1/kappa; % 曲率半径 [mm] 
% Mom_slope = Stabbing_Momentum * kappa; % ニードルのカッティングにより生じる進行方向の傾き(x軸周り,z軸変位に対する割合)[rad] 村上修正(2024/08/16)
% Mom_Vec_tt = rho * [0,-(1 - cos(Mom_slope)),sin(Mom_slope)] + disturbance; % ニードルの進行ベクトル(ニードル先端慣性座標基準)
% 
% % omega >> Stabbing_Velという前提があるので、theta_deltaの更新後に回転行列R_tb_new及び刺入変位量Mom_Vec_tbを計算
% gamma = Needle_pose(4); % [rad]
% phi   = Needle_pose(5); % [rad]
% theta       = Needle_pose(6);% [rad]
% 
% Rx = Cal_Rotation_Matrix(gamma,R_axis.x);
% Ry = Cal_Rotation_Matrix(phi  ,R_axis.y);
% Rz = Cal_Rotation_Matrix(theta,R_axis.z);
% R_tb = Rz * Ry * Rx;
% 
% Rz_delta = Cal_Rotation_Matrix(theta_delta,R_axis.z);
% R_tb_new = R_tb * Rz_delta;
% 
% 
% Mom_Vec_tb = R_tb_new * Mom_Vec_tt'; % 式(3)を参考にすると、tip→targetからbese→targetへの変換は、逆行列無しの回転行列で良いと推測
%                                      % また、あくまで速度ベクトルなので、位置情報を含む同次変換行列も不要と想定
% 
% % ニードル位置を更新
% x_new = Needle_pose(1) + Mom_Vec_tb(1);
% y_new = Needle_pose(2) + Mom_Vec_tb(2);
% z_new = Needle_pose(3) + Mom_Vec_tb(3);
% 
% % ニードル姿勢を更新(ChatGPTを参考にコードを修正20240530)
% delta_gamma = Mom_slope; % カッティングにより、ニードルは刺入しながらx軸回りにMom_slopeだけ回転すると想定
% R_x_delta = Cal_Rotation_Matrix(delta_gamma,R_axis.x);
% R_new_delta = R_tb_new * R_x_delta;
% 
% % gamma_new = atan2(R_new(3,2), R_new(3,3));
% % phi_new = atan2(-R_new(3,1), sqrt(R_new(3,2)^2 + R_new(3,3)^2));
% eul_new = rotm2eul(R_new_delta,'ZYX');
% gamma_new = eul_new(3);
% phi_new   = eul_new(2);
% theta_new = theta + theta_delta; % [rad]
% 
% % 更新後のニードル位置姿勢をまとめる
% Needle_pose_new = [x_new, y_new, z_new, gamma_new, phi_new, theta_new];


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Faridの幾何学運動模擬 %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

du1 = Stabbing_Vel * Time_resolution;
du2 = omega * Time_resolution;

Gab0 = Gen_pose2tform(Needle_pose);

% Bicycle model configurations（引用）
% Unit Vectors
e1 = [1;0;0];
e2 = [0;1;0];
e3 = [0;0;1];

% Geometric Relations
%mm
l2 = 0;%23.775; mm For unicycle model this will be zero
V1 = [e3; max_curvature * e1];
V2 = [zeros(3,1); e3];

% 同時変換行列を使ったユニモデルの位置/姿勢計算
[Gab, Needle_tip_position] = bicycleKinematicsModel(Gab0,du1, du2, V1,V2,l2, e3);

Gab(1:3,4) = Gab(1:3,4) + disturbance'; % Additional disturbance
% Gab(1:3,4) = Gab(1:3,4) .* disturbance'; % Proportional disturbance
Needle_pose_new = Gen_tform2pose(Gab);
% Needle_pose_new(1:3) = Needle_tip_position'; % これを適用すると、初期値から更新されなくなった（20241109_mori）

Mom_Vec_tb = Gab(1:3,4) - Gab0(1:3,4);

Needle_pose_new(6) = Needle_pose(6) + du2;

end

