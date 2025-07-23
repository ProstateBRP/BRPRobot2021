function state_new = stateTransitionModel(state, u, dt)
    % 状態遷移関数
    % x: 状態ベクトル (Needle_pose: [x, y, z, gamma, phi, theta])
    % u: 入力ベクトル ([omega, Stabbing_Vel])
    % dt: 時間分解能 (Time_resolution)

    omega = u(1);
    Stabbing_Vel = u(2);
    Needle_pose = state;
    Time_resolution = dt;

    % モデル誤差パラメータ設定
    scale_model = 1.0;

    % 外乱要素
    disturbance = [0,0,0];

    state_new = Update_Needle_pose_select(omega, Stabbing_Vel, Time_resolution, Needle_pose,scale_model,disturbance);
    state_new = state_new';

    % % % ニードルの回転量を計算
    % % theta_delta = omega * Time_resolution; % [rad]
    % % theta = Needle_pose(6); % [rad]
    % % 
    % % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % % %%% ↓は全て要確認。多分大幅に間違えてる(20240511) %%%
    % % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % % 
    % % % ニードルの刺入量を計算(ニードル先端慣性座標基準)
    % % Stabbing_Momentum = Stabbing_Vel * Time_resolution;
    % % Mom_slope = 1/180 * pi /20; % ニードルのカッティングにより生じる進行方向の傾き(x軸周り)[rad] 仮置き(20240511)
    % % Mom_Vec_tt = Stabbing_Momentum * [0, -sin(Mom_slope), cos(Mom_slope)]; % ニードルの進行ベクトル(ニードル先端慣性座標基準)
    % % 
    % % % omega >> Stabbing_Velという前提があるので、theta_deltaの更新後に回転行列R_tb_new及び刺入変位量Mom_Vec_tbを計算
    % % gamma = Needle_pose(4); % [rad]
    % % phi = Needle_pose(5); % [rad]
    % % 
    % % Rx = Cal_Rotation_Matrix(gamma, R_axis.x);
    % % Ry = Cal_Rotation_Matrix(phi, R_axis.y);
    % % Rz = Cal_Rotation_Matrix(theta, R_axis.z);
    % % R_tb = Rz * Ry * Rx;
    % % 
    % % Rz_delta = Cal_Rotation_Matrix(theta_delta, R_axis.z);
    % % R_tb_new = R_tb * Rz_delta;
    % % 
    % % Mom_Vec_tb = R_tb_new * Mom_Vec_tt'; % 式(3)を参考にすると、tip→targetからbese→targetへの変換は、逆行列無しの回転行列で良いと推測
    % % % また、あくまで速度ベクトルなので、位置情報を含む同次変換行列も不要と想定
    % % 
    % % % ニードル位置を更新
    % % x_new = Needle_pose(1) + Mom_Vec_tb(1);
    % % y_new = Needle_pose(2) + Mom_Vec_tb(2);
    % % z_new = Needle_pose(3) + Mom_Vec_tb(3);
    % % 
    % % % ニードル姿勢を更新(ChatGPTを参考にコードを修正20240530)
    % % delta_gamma = Mom_slope; % カッティングにより、ニードルは刺入しながらx軸回りにMom_slopeだけ回転すると想定
    % % R_x_delta = Cal_Rotation_Matrix(delta_gamma, R_axis.x);
    % % R_new_delta = R_tb_new * R_x_delta;
    % % 
    % % % gamma_new = atan2(R_new(3,2), R_new(3,3));
    % % % phi_new = atan2(-R_new(3,1), sqrt(R_new(3,2)^2 + R_new(3,3)^2));
    % % eul_new = rotm2eul(R_new_delta, 'ZYX');
    % % gamma_new = eul_new(3);
    % % phi_new = eul_new(2);
    % % theta_new = theta + theta_delta; % [rad]
    % % 
    % % % 更新後のニードル位置姿勢をまとめる
    % % state_new = [x_new, y_new, z_new, gamma_new, phi_new, theta_new];

end
