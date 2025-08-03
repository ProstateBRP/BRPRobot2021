function [ekf,Pred_State] = Update_EKF(ekf,Needle_pose_sensor,sensor_flag,omega_All,Stabbing_Vel,Freq_ctrl_sec,Ctrl_Step_num,delay_step_CtrlFreq)
% UPDATE_EKF　カルマンフィルタの内部状態を更新する
% input：
%   ekf_in             - 入力時のEKF 
%   Needle_pose_sensor - ニードル先端位置/角度
%   sensor_Freq        - センシング周期フラグ
%   Us                 - 状態遷移関数の追加入力引数Us
%   delay_Ctrl_step    - 制御周期を考慮したセンサ遅延ステップ
% output：
%   ekf_out     - 

% delya_step_CtrlFreq先予測のために、Us.uを定義
% 具体的には、omega_ekf(1)がdelay_ste_CtrlFreq前の制御出力、omega_ekf(end)が最新の制御出力となるようにしている
if Ctrl_Step_num <= delay_step_CtrlFreq + 1
    omega_ekf = [zeros(delay_step_CtrlFreq - Ctrl_Step_num + 2,1);omega_All(1:Ctrl_Step_num-1)'];
    Vel_ekf   = Stabbing_Vel * [zeros(delay_step_CtrlFreq - Ctrl_Step_num + 2,1);ones(Ctrl_Step_num - 1,1)];
else
    omega_ekf = omega_All(Ctrl_Step_num - delay_step_CtrlFreq - 1:Ctrl_Step_num - 1)';
    Vel_ekf   = Stabbing_Vel * ones(delay_step_CtrlFreq + 1,1);
end
Us.u = [omega_ekf,Vel_ekf]; % 状態遷移関数の追加入力引数(1)
Us.dt = Freq_ctrl_sec;      % 状態遷移関数の追加入力引数(2)

% 状態の予測（開発中）
[Pred_State,~] = predict(ekf,Us.u(1,:),Us.dt);
% Pred_State = Pred_State';


% センシング周期の場合、EKFをcorrectで補正
if sensor_flag == true
    % カルマンフィルタに使用するための出力を計算
    Y_out = measurementFcn(Needle_pose_sensor);
    
    % カルマンフィルタによる状態の補正
    correct(ekf, Y_out);
end

% delay_step_CtrlFreq分、先の状態を推定
ekf_tmp = clone(ekf);
for i = 1:delay_step_CtrlFreq
    [Pred_State,~] = predict(ekf_tmp,Us.u(i+1,:),Us.dt);
end

end

