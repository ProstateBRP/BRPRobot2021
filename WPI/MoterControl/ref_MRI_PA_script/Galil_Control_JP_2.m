%% Galil Control Main
% Currently, only focus on Inner Shaft and its encoder
% Last updated: March.9 2024

% Revision Log %
% Dec. 5: Switched DO 1 & DO 2 based on wiring inside control box
% Dec. 9: Added "global_count" for encoder logging
% Dec. 18: Accelarate control loop
% April. 18, 2023: Modify to follow Yichuan's protocol (no trigger from scan code. time-based sequence control)
% April. 22, 2023: Add homing function for 3D US
% March. 9, 2024: Modify homing feature to avoid backrush

%% Description

% Pin Map (new)
% DO 1: Inner CCW
% DO 2: Inner CW
% DO 3: Inner Power
% DO 4: Outer CW
% DO 5: Outer CCW
% DO 6: Outer Power

% Analog out1: Inner velocity control
% Analog out2: Outer velocity control

% Use control with "Galiil_control_command.m"
% Initialize GUI before running this code

%% Initialization
disp('Code initiated')

clear all
close all
clc

% fig = figure; % Figure for callback
% fig.KeyPressFcn = @my_callback;
addpath /PALap_Ryo
mode_flag = 1;
key = "ini";
vel_manual = 2; % [V]
duration_vel_linear = 0.5; % sec
% duration_vel_linear = 10; % sec
duration_vel_linear_auto = 0.01; % sec
% duration_vel_plateu = 0.2; % sec % Uncomment
duration_vel_plateu = 0.5; % sec % Only for test
duration_vel_plateu_auto = 1/100; % sec % Uncomment
% duration_vel_plateu_auto = 2; % sec % Only for test
resolution_vel_linear = 100; % step
pause_turnoff = 0.1; % sec
pause_turnon = 0.1; % sec
pause_safety = 2; % sec
vel_auto = 0.01; % [V]
% flag_dir_auto = 0;
% encoder_err_allowance = 5; % tic
encoder_err_allowance = 10;
count_now = -1;
encoder_CPR = 5000*8; 
duration_prep_rot = 0.01;
Angle_registration = 90; % deg
global_count = 0;
count_A_log = [];
count_B_log = [];

count_down_num = 1;
disp(['Turn on power for controller (pause',num2str(count_down_num),'seconds)'])
count_down(count_down_num);

if not(isfolder("PALap_Ryo\EncoderInfo"))
    mkdir("PALap_Ryo\EncoderInfo")
end

%% Communication Setup
g = actxserver('galil');
response = g.libraryVersion;
disp(response);

g.address ='';
response = g.command(strcat(char(18),char(22)));
disp(strcat('Connected to: ',response));

response = g.command('MG_BN');
disp(strcat('Serial Number: ',response));

% save('PALap_Ryo/realtime.mat')
%% Control module initialization

% Turn off DO1 and DO2 (Safety feature)
response = g.command('CB 1');
response = g.command('CB 2');
response = g.command('CB 3');
response = g.command('CB 4');
response = g.command('CB 5');

disp('Prepare Relays to drivers')
% disp('> Accessing to Relay1 for Inner')
disp('> Accessing to Relay for Inner & Outer')
response = g.command('SB 3');
% disp('> Accessing to Relay2 for Outer')
% response = g.command('SB 6');
disp('Relay for drivers should be turned on')

%% Power for drivers
disp(['Turn on power for drivers (pause',num2str(count_down_num),'seconds)'])
count_down(count_down_num);

%% Main
angle_range = 180; % deg
angle_step = 1; % deg
angle_step_count = deg2enccount(angle_step,encoder_CPR);
angle_range_count = deg2enccount(angle_range,encoder_CPR);

count_step = 0;
angle_start = nan;

pause_duration = 0.01;

while true    
    global_count = global_count + 1;
    try
        copyfile('PALap_Ryo/realtime.mat','PALap_Ryo/realtime_readback.mat' )
    catch
        disp('load error > skip')
    end
        load('PALap_Ryo/realtime_readback.mat',"val_struct")  
    
%         disp('-----Data reading-----')
    try
        copyfile('PALap_Ryo/realtime_3d.mat','PALap_Ryo/realtime_3d_readback.mat' )
    catch
        disp('load error 3d > skip')
    end
    load('PALap_Ryo\realtime_3d_readback.mat','key_3d','mode_flag_3d');
%     key_3d
%     mode_flag_3d
%     disp('-----Data reading end-----')
    
    count_step = val_struct.count;
    key = val_struct.key;
    mode_flag = val_struct.mode_flag;
    vel_manual = val_struct.vel_manual;
    vel_auto = val_struct.vel_auto;
    angle_manu = val_struct.angle_manu;

    count_now = g.command('TPA'); % Inner shaft % Uncomment
    if key == 'n' && mode_flag == 0
        disp('Initialization')
        
        mode_flag = 00;
    elseif key == "o" && mode_flag == 1
        disp('Outer: Rotate CW')                
        count_now_B = str2double(g.command('TPB'));
        count_t_manu = count_now_B + abs(deg2enccount(angle_manu,encoder_CPR));
        diff = encoder_FB(g,count_t_manu,4,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);                           
        mode_flag = 11;

    elseif key == "i" && mode_flag == 2
        disp('Outer: Rotate CCW')
        count_now_B = str2double(g.command('TPB'));
        count_t_manu = count_now_B - abs(deg2enccount(angle_manu,encoder_CPR));
        diff = encoder_FB(g,count_t_manu,5,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);               
        mode_flag = 22;

    elseif key == "l" && mode_flag == 3
        disp('Inner: Rotate CW')
        count_now = str2double(g.command('TPA'));
        count_t_manu = count_now - abs(deg2enccount(angle_manu,encoder_CPR));
%         diff = encoder_FB(g,count_t_manu,1,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot); 
        diff = encoder_FB(g,count_t_manu,2,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR); 
        mode_flag = 33;
    
    elseif key == "k" && mode_flag == 4
        disp('Inner: Rotate CCW')
        count_now = str2double(g.command('TPA'));
        count_t_manu = count_now + abs(deg2enccount(angle_manu,encoder_CPR));
%         diff = encoder_FB(g,count_t_manu,2,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot);
        diff = encoder_FB(g,count_t_manu,1,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);
        mode_flag = 44;

    elseif key_3d == 's' && mode_flag_3d == 5 % Push after each scan
        count_step = count_step + 1        
        
%         disp('Start step rotation for scan');
        count_target = angle_start - angle_step_count*count_step;
%         diff = encoder_FB(g,count_target,1,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot);    
        diff = encoder_FB(g,count_target,2,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);  
        error_log(count_step) = diff; % Store error log
        
        mode_flag = 55;
%         mode_flag_3d = 55;
        count_step
    %{
        % Only for 3D US slow
        elseif key == 's' && mode_flag == 5 % Push after each scan
        count_step = count_step + 1        
        disp('slow')
%         disp('Start step rotation for scan');
        count_target = angle_start - angle_step_count*count_step;
%         diff = encoder_FB(g,count_target,1,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot);    
        diff = encoder_FB(g,count_target,2,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot);  
        error_log(count_step) = diff; % Store error log
        
        mode_flag = 55;
%         mode_flag_3d = 55;
        count_step
    %}
    elseif key == 'r' && mode_flag == 6 % Push when the initial alighnment is finished (Define the start angle and move to it)
        disp('Position registered')
        angle_temp = str2double(g.command('TPA')); % Uncomment outside testing
        count_now = angle_temp;
        angle_start = angle_temp + deg2enccount(Angle_registration,encoder_CPR); 
        diff = encoder_FB(g,angle_start,1,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);                

        mode_flag = 66;
    
    elseif key == 'c' && mode_flag == 8
        response = g.command('CB 1');
        response = g.command('CB 2');
        response = g.command('CB 3');
        response = g.command('CB 4');
        response = g.command('CB 5');
        response = g.command('OFA=0');
        response = g.command('OFB=0');
        disp('Turned off all the output ports')
        mode_flag = 88;

    elseif key == 'q' && mode_flag == 7
        disp('Terminate the backend program')
        response = g.command('CB 1');
        response = g.command('CB 2');
        response = g.command('CB 3');
        response = g.command('CB 4');
        response = g.command('CB 5');
        response = g.command('OFA=0');
        response = g.command('OFB=0');
        save('PALap_Ryo\EncoderInfo/count_log.mat',"count_A_log","count_B_log")
        delete(g);
        mode_flag = 77;
        close all
        clear all
        break
    elseif key == 't' && mode_flag == 9
        disp('Started time-based sequence control')

        % set sequence control parameters
        frame_total = 182;
        num_WL = 1;
        frame_num_per_WL = 32;
%         frame_num_per_WL = 1;
        freq_laser = 20; % [Hz]
%         data_acq_time = (num_WL*frame_num_per_WL)/freq_laser; % [sec/slice]
        data_acq_time = 1.5; % for 3D US
        flag_measure_time = 0;
        stabilization_time = 0.5; % [sec] *should be tuned (if pursuing safety, total time should be more than data_acq_time*2 && should be "nearly" irrational number)
        motor_actuation_time = 0.17; % [sec] *just for reference (not used for control)
        (data_acq_time+motor_actuation_time+stabilization_time)*frame_total/(frame_num_per_WL*num_WL/freq_laser)
        for frame_num = 1:frame_total
            % record time tag
            time = clock;
            name_time = ['time_tag_motor_',num2str(frame_num)];
            eval([name_time,' = time;']);
            if frame_num == 1
                save('PALap_Ryo\EncoderInfo/time_tag_motor.mat',name_time,'-v6');
            else 
                save('PALap_Ryo\EncoderInfo/time_tag_motor.mat',name_time,'-v6','-append');
            end

            % record encoder reading
            name_encoder = ['encoder_read_',num2str(frame_num)];
            encoder_read = str2double(g.command('TPA')); % Uncomment outside testing
            eval([name_encoder,' = encoder_read;']);
            if frame_num == 1
                save('PALap_Ryo\EncoderInfo/encoder_read_3D.mat',name_encoder,'-v6');
            else 
                save('PALap_Ryo\EncoderInfo/encoder_read_3D.mat',name_encoder,'-v6','-append');
            end

            % pause for staying at one position
            disp('Pausing for Data Acquisition')
            pause(data_acq_time);
            disp('----------------------------')

            % calculate the next angle
            count_step = frame_num;
            count_target = angle_start - angle_step_count*count_step;

            % move to the next angle
            if flag_measure_time == 1
                tic
            end
            disp(['Moving to Angle #',num2str(count_step)]);
            diff = encoder_FB(g,count_target,2,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);  
            disp('----------------------------')
            if flag_measure_time == 1
                toc
            end
            disp('----------------------------')
            disp('Start stabilization')
            pause(stabilization_time)
            disp('Finished stabilization')
            disp('----------------------------')

        end

        disp('Terminated: Time-based sequence control')
        disp('----------------------------')
        break
    
    elseif key == 'u' && mode_flag == 11 % Push when the initial alighnment is finished (Define the start angle and move to it)
        disp('Homing start')
        angle_temp = str2double(g.command('TPA')); % Uncomment outside testing
        count_now = angle_temp;
        angle4backrush = 30; % deg
        count4backrush = deg2enccount(angle4backrush,encoder_CPR);
        angle_start = 0;
        if count_now > 0
            flag_direction = 2;
        else
            flag_direction = 1;
        end
        
        disp('Going back to Origin...')
        diff = encoder_FB(g,angle_start,flag_direction,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);                
        
        disp('Backrush prevention (Rotate back and forth)')
        pause(1)
        % Negative or Positive?
        diff = encoder_FB(g,angle_start + count4backrush,1,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);
        pause(1)
        diff = encoder_FB(g,angle_start,2,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR);

        disp('Homing finished')
        mode_flag = 111;
    end
    
    count_now = str2double(g.command('TPA')); % Uncomment outside testing
    count_now_B = str2double(g.command('TPB'));
%     disp(['Current tic A axis: ',num2str(count_now)])
%     disp(['Current tic B axis: ',num2str(count_now_B)])
    val_struct.key = key;
    val_struct.mode_flag = mode_flag;
    val_struct.count = count_step;
    save('PALap_Ryo/realtime_outback.mat',"val_struct")
    copyfile('PALap_Ryo/realtime_outback.mat','PALap_Ryo/realtime.mat' )
%     save('PALap_Ryo/realtime_3d_back.mat',"key_3d",'mode_flag_3d')
%     copyfile('PALap_Ryo/realtime_3d_out.mat','PALap_Ryo/realtime_3d.mat' )
    
    % Status visualization
    if mode_flag == 00
%         disp('Current status: After Initialization')
    elseif mode_flag == 11
%         disp('Current status: After OUT CW')
    elseif mode_flag == 22
%         disp('Current status: After OUT CCW')
    elseif mode_flag == 33
%         disp('Current status: After IN CW')
    elseif mode_flag == 44
%         disp('Current status: After IN CCW')
    elseif mode_flag == 55
%         disp('Current status: Scaning')
    elseif mode_flag == 66
        disp('Current status: After Registration')
    elseif mode_flag == 88
%         disp('Current status: After Kill backend communication')
    end
    
    count_A_log(global_count) = str2double(g.command('TPA'));
    count_B_log(global_count) = str2double(g.command('TPB'));
%     disp('-----Input waiting------')
%     pause(1/50) %3D PA (original: 1/1000)
%     pause(1/2) %3D US narrow
    pause(2/3) % 3D US wide
    
% 
end

save('PALap_Ryo\EncoderInfo\log.mat'); % Save all

disp('Code terminated');

% Custom function for conversion from degree to count
function count_num = deg2enccount(deg_target,encoder_CPR)

    count_num = encoder_CPR/360*deg_target; % count

end

% Custom function for linear speed profiling
function speed_profile_linear(hg,INorOut,t_st,t_ed,vel_st,vel_ed)        
    
    disp('Start Linear speed control')
    time_step = 0.01;
    vel_slope = (vel_ed - vel_st)/(t_ed - t_st);
    vel_inter = (vel_st*t_ed - t_st*vel_ed)/(t_ed - t_st);
    
    for count_step=t_st:time_step:t_ed
        voltage = vel_slope*count_step + vel_inter
        if INorOut=="IN"
            response = hg.command(['OFA=',num2str(voltage)]);   
        elseif INorOut=="OUT"
            response = hg.command(['OFB=',num2str(voltage)]);
        end
        pause(time_step);
    end
    disp('Terminate Linear speed control')
end

% Custom function for count down
function count_down(time)
    for pwt=time:-1:1
        disp(['Remaining:',num2str(pwt)])
        pause(1)
        if pwt==1
            disp('End')
        end
    end
end

% Custom function for encoder feedback rotation
function diff = encoder_FB(g,count_t,DO_num,encoder_err_allowance,vel_auto,pause_turnoff,duration_prep_rot,encoder_CPR)
        
        disp('Rotation Start')

        if DO_num == 1
            DO_num_opposite = 2;
        elseif DO_num == 2
            DO_num_opposite = 1;
        elseif DO_num == 4
            DO_num_opposite = 5;
        elseif DO_num == 5
            DO_num_opposite = 4;
        end
               
        if DO_num == 1 || DO_num == 2
            command_encoder = 'TPA';
            command_analog = 'OFA=';
        elseif DO_num == 4 || DO_num == 5
            command_encoder = 'TPB';
            command_analog = 'OFB=';
        end
        
        count_now = str2double(g.command(command_encoder));
        disp(['Current Count: ',num2str(count_now)])

        if count_now - count_t >= 0
            diff = count_now - count_t;
            diff_flag = 1;
        else
            diff = count_t - count_now;
            diff_flag = 2;
        end

        command_true = ['SB ',num2str(DO_num)];
        command_false = ['CB ',num2str(DO_num)];
        
        

        command_false_opposite = ['CB ',num2str(DO_num_opposite)];
        
        response = g.command(command_false_opposite);
        response = g.command([command_analog,num2str(vel_auto)]);
%         disp('Prepare for rotation')
        pause(duration_prep_rot)
        
        fprintf('\n');
        while diff > encoder_err_allowance
            response = g.command(command_true);
%             tic
            count_now = str2double(g.command(command_encoder));             
%             toc            
            if diff_flag == 1
                diff = count_now - count_t;
            elseif diff_flag == 2
                diff = count_t - count_now;
            end

            % safety feature (added on April 19, 2023)
            if abs(count_now) > deg2enccount(360*1.5,encoder_CPR)
                break;
            end
        end

        response = g.command(command_false);
        response = g.command(command_false_opposite);
        response = g.command([command_analog,num2str(0)]);
        pause(pause_turnoff)

%         disp('Reached Target Position')        
        count_now = str2double(g.command(command_encoder));
        disp(['Current Count: ',num2str(count_now)])
        if diff_flag == 1
            diff = count_now - count_t;
        elseif diff_flag == 2
            diff = count_t - count_now;
        end

%         disp(['Final Error: ',num2str(diff), '[tic]'])
        
        disp('Rotation Terminated')
end
