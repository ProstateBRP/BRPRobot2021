%% Create GalilTools COM server object
g = init_galil();

%% Control Module Initialization
% Access Relay
g.command('SB 3');
pause(0.1);
disp('Relay for drivers should be turned on');

% %% Test Insert
% voltage = 2;
% direction = 1;
% move_insertion(g, direction, voltage);
% pause(2);
% stop_insertion(g, direction);
% 
% ticks = get_encoder_insertion(g);
% disp(num2str(ticks));
% 
% %% Test Pull-out
% voltage = 2;
% direction = 0;
% move_insertion(g, direction, voltage);
% pause(5)
% stop_insertion(g, direction);
% 
% ticks = get_encoder_insertion(g);
% disp(num2str(ticks));

%% Insertion Speed Calibration
PPR = 5000;

voltage_st = 2.28;
voltage_res = 0.01;
voltage_step_num = 3;
voltage_ed = voltage_st + voltage_res*(voltage_step_num-1);

disp("Calibrating Insert Direction");
direction = 1;
calibrate_speed(g, direction,voltage_st,voltage_ed,voltage_res);


disp("Calibrating Pull-out Direction");
direction = 0;
calibrate_speed(g, direction,voltage_st,voltage_ed,voltage_res);


function calibrate_speed(g, direction,voltage_st,voltage_ed,voltage_res)
    for voltage = voltage_st:voltage_res:voltage_ed
        disp("Voltage: " + string(voltage));
        move_insertion(g, direction, voltage);
        pause(0.5);
    
        start_time = tic;
        start_ticks = get_encoder_insertion(g);
        pause(0.5);
        elapsed_time = toc(start_time);
        end_ticks = get_encoder_insertion(g);
        insertion_speed = (end_ticks - start_ticks) / 5000 * 3 / elapsed_time;
        disp("Insertion Speed: " + string(insertion_speed))
        stop_insertion(g, direction);
        pause(0.5);
    end
end




