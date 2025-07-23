function [] = plot_NeedleTrace3D(Needle_pose_All,Needle_pose_act_All,Mom_Vec_All, Target_Pos,flag_mov)
% PLOT_NEEDLETRACE3D ニードルの軌跡を描画する
%

% ニードルの位置姿勢情報を抽出
N_x = squeeze(Needle_pose_All(:,1));
N_y = squeeze(Needle_pose_All(:,2));
N_z = squeeze(Needle_pose_All(:,3));
% N_gamma = Needle_pose_All(2,1,:);
% N_phi   = Needle_pose_All(2,2,:);
% N_theta = Needle_pose_All(2,3,:);
N_x_act = squeeze(Needle_pose_act_All(:,1));
N_y_act = squeeze(Needle_pose_act_All(:,2));
N_z_act = squeeze(Needle_pose_act_All(:,3));


% ニードルの進行方向ベクトルを生成
V_x = squeeze(Mom_Vec_All(:,1));
V_y = squeeze(Mom_Vec_All(:,2));
V_z = squeeze(Mom_Vec_All(:,3));

% ターゲットの位置情報を抽出
T_x = Target_Pos(1);
T_y = Target_Pos(2);
T_z = Target_Pos(3);

num_frame_tmp1 = size(Needle_pose_All,1);
num_frame_tmp2 = size(Needle_pose_act_All,1);
num_frame = min(num_frame_tmp1,num_frame_tmp2);

if flag_mov == 1
    % 動画オブジェクト作成
    % outputVideo = VideoWriter('myVideo.mp4', 'MPEG-4');
    outputVideo = VideoWriter('myVideo.avi');
    open(outputVideo);
    frameRate = 30;
    % outputVideo.FrameRate = frameRate;

    st_frame = 1;
    step_frame = 5;

else
    st_frame = num_frame;
    step_frame = 1;
end


for count_frame=st_frame:step_frame:num_frame

    vec_plot = st_frame:step_frame:count_frame;

    % グラフ描画
    h_result = figure(1);
    % quiver3(N_x, N_y, N_z, V_x, V_y, V_z, 1) % ニードル位置姿勢
    plot3(N_x(vec_plot), N_y(vec_plot), N_z(vec_plot),'LineWidth',2) % ニードル位置姿勢
    hold on
    plot3(N_x_act(vec_plot), N_y_act(vec_plot), N_z_act(vec_plot),'Color','m','LineWidth',1) % ニードル位置姿勢
    scatter3(T_x,T_y,T_z,'filled','MarkerEdgeColor','k','MarkerFaceColor',[0 .75 .75]) % ターゲット位置
    xlabel('x [mm]')
    ylabel('y [mm]')
    zlabel('z [mm]')
    axis equal
    grid on
    title(num2str(count_frame))
    hold off

    if flag_mov == 1
        frame_temp = getframe(h_result);
        writeVideo(outputVideo,frame_temp);
    end
    % exportgraphics(h_result,'result/graph.png','Resolution',600);

end

if flag_mov == 1
    close(outputVideo);
end

end

