function [] = plot_Kalman_Observer(Needle_pose_All,Needle_pose_sensor_All,Needle_pose_act_All, Target_Pos,Freq_ctrl_sec, Freq_sens_sec, delay_rem)
% plot_Kalman_Observer カルマンフィルタによる推定結果(外挿及び内挿)を表示する
%

% % ニードルの位置姿勢情報(センサ)を抽出
% N_x = squeeze(Needle_pose_sensor_All(:,1));
% N_y = squeeze(Needle_pose_sensor_All(:,2));
% N_z = squeeze(Needle_pose_sensor_All(:,3));
% 
% % カルマンフィルタの推定情報を抽出
% N_x_act = squeeze(Needle_pose_act_All(:,1));
% N_y_act = squeeze(Needle_pose_act_All(:,2));
% N_z_act = squeeze(Needle_pose_act_All(:,3));
% 
% % ターゲットの位置情報を抽出
% T_x = Target_Pos(1);
% T_y = Target_Pos(2);
% T_z = Target_Pos(3);

time_ctrl   = Freq_ctrl_sec*(0:size(Needle_pose_act_All,1)-1);
time_update = Freq_ctrl_sec*(0:size(Needle_pose_All,1)-1);
time_sens   = Freq_sens_sec*(0:size(Needle_pose_sensor_All,1)-1) - delay_rem;
Ylabel_str = {'X[mm]','Y[mm]','Z[mm]','Rx[rad]','Ry[rad]','Rz[rad]'};
filename   = {'Xfig','Yfig','Zfig','Rxfig','Ryfig','Rzfig'};
Target_Pos = [Target_Pos,0,0,0];
for axis_num = 1:6

    % グラフ描画
    h_result = figure(axis_num);
    plot(time_ctrl, squeeze(Needle_pose_act_All(:,axis_num)),'Color','m','LineWidth',2.5) % カルマンフィルタ推定値
    hold on
    plot(time_update, squeeze(Needle_pose_All(:,axis_num)),'Color','b','LineWidth',1) % シミュレーション実測値
    scatter(time_sens,squeeze(Needle_pose_sensor_All(:,axis_num)),'filled','MarkerEdgeColor','b','MarkerFaceColor','b') % センサ出力
    scatter(time_ctrl(end),Target_Pos(axis_num),'filled','MarkerEdgeColor','k','MarkerFaceColor',[0 .75 .75]) % ターゲット位置
    xlabel('time [sec]')
    ylabel(Ylabel_str{axis_num})
    xlim([0,time_ctrl(end)])
    grid on
    title(Ylabel_str{axis_num})
    hold off

    saveas(gcf,[filename{axis_num},'.png'])

end

end
