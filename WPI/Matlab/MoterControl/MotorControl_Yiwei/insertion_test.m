%% Create GalilTools COM server object
g = init_galil();

%% Set A, B Port as Servo
response = g.command('MT 1,1,1');
response = g.command('KP 0,0,0');
response = g.command('KI 0,0,0');
response = g.command('KD 0,0,0');
response = g.command('SH A');

% response = g.command('MT 1');
% response = g.command('KP 0');
% response = g.command('KI 0');
% response = g.command('KD 0');
response = g.command('SH B');
response = g.command('SH C');

% response = g.command('OFB=3');

% Turn off DO1 and DO2 (Safety feature)
response = g.command('CB 1');
response = g.command('CB 2');
response = g.command('CB 3');
response = g.command('CB 4');
response = g.command('CB 5');

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

voltage_st = 2.14;
voltage_res = 0.02;
voltage_step_num = 3;
voltage_ed = voltage_st + voltage_res*(voltage_step_num-1);

disp("Calibrating Insert Direction");
direction = 1;
calibrate_speed(g, direction,voltage_st,voltage_ed,voltage_res);


disp("Calibrating Pull-out Direction");
direction = 0;
calibrate_speed(g, direction,voltage_st,voltage_ed,voltage_res);

disable_galil(g)


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




