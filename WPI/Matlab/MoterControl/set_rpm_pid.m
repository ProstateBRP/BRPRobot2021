function set_rpm_pid(g, motor_num, direction, desired_rpm, max_error)
    % PID Controller for desired RPM
    kp = 0.01; % Proportional gain
    ki = 0.00001; % Integral gain
    kd = 0.00001; % Derivative gain

    integral = 0;
    previous_error = 0;
    
    % Encoder configuration
    ticks_per_rev = 5000; % Encoder ticks per revolution

    % Initialize control variables
    speed_volt = 0;
    error = Inf;
    
    % Initialize data storage for plotting
    time_values = [];
    rpm_values = [];

    % Get initial encoder reading
    loop_start = tic;
    prev_ticks = get_encoder_ticks(g, motor_num);
    
    control_period = 1/20; % 20 Hz control loop

    try
        while abs(error) > max_error
            % Read current encoder count
            current_ticks = get_encoder_ticks(g, motor_num);

            % Calculate current RPM
            elapsed_time = toc(loop_start);
            ticks_per_sec = (current_ticks - prev_ticks) / elapsed_time;
            current_rpm = (ticks_per_sec / ticks_per_rev) * 60;
            if direction == 1
                current_rpm = -current_rpm;
            end

            % Store data for plotting
            time_values = [time_values, elapsed_time];
            rpm_values = [rpm_values, current_rpm];

            % PID control calculations
            error = desired_rpm - current_rpm;
            integral = integral + error * elapsed_time;
            derivative = (error - previous_error) / elapsed_time;

            % Calculate and limit control output 
            control_output = kp * error + ki * integral + kd * derivative;
            speed_volt = min(3.3, max(0, speed_volt + control_output));

            % Set motor direction and speed
            set_vel_volt(g, motor_num, direction, speed_volt);

            % Update previous values
            previous_error = error;
            prev_ticks = current_ticks;
            loop_start = tic;

            % Maintain control loop timing
            elapsed = toc(loop_start);
            if elapsed < control_period
                pause(control_period - elapsed);
            end
        end
    catch ME
        disp(['Error occurred during RPM monitoring: ', ME.message]);
    end
end

function ticks = get_encoder_ticks(g, motor_num)
    if motor_num == 3
        ticks = str2double(g.command('TPA'));
    elseif motor_num == 6
        ticks = str2double(g.command('TPB'));
    end
end
