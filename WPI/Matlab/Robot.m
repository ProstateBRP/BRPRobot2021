classdef Robot < handle
    %ROBOT - Advanced needle insertion robot controller
    % 
    % This class provides comprehensive control for needle insertion robots
    % including registration, planning, targeting, movement control, and
    % real-time feedback processing.
    %
    % USAGE:
    %   Normal mode (requires hardware):
    %     rob = robot();
    %     rob = rob.startup();
    %
    %   Simulation mode (no hardware required):
    %     rob = robot('simulation', true);
    %     rob = rob.startup();
    %
    %   Switch to simulation mode after creation:
    %     rob = robot();
    %     rob = rob.enable_simulation_mode();
    %     rob = rob.startup();
    %
    % SIMULATION MODE:
    %   - Bypasses hardware initialization (Arduino, Galil)
    %   - Uses simulated sensor values
    %   - Skips actual motor control
    %   - Allows testing of control algorithms and flow

    properties (Access = private)
        %% ===================================================================
        %  BASIC ROBOT STATE PROPERTIES
        %% ===================================================================
        current_mode = 'stop'                          % Current robot operation mode
        is_start_up = false                            % Current robot started up or not
        starting_position                               % Initial robot position
        target_position_robot                           % Target position in robot frame
        is_target_reached                              % Flag indicating if target is reached
        previou_needle_pose_MRI                        % Previous needle pose from MRI
        simulation_mode = false                        % Flag to enable simulation mode
        
        %% ===================================================================
        %  REGISTRATION AND COORDINATE TRANSFORMATION
        %% ===================================================================
        registration_matrix = [1, 0., 0., 0.; 0., 1, 0., 0.; 0., 0., 1, 0.; 0., 0., 0., 1]
        validModes = ['startup', 'calibration', 'planning', 'targeting', 'idle', 'move_to_goal', 'stop'];

        %% ===================================================================
        %  NEEDLE CONTROL PARAMETERS
        %% ===================================================================
        Needle_pose_ini = [0, 0, 0, 0, 0, 0]          % Initial needle pose [x,y,z,gamma,phi,theta] (mm,rad)
        Target_Pos_local                               % Target position in needle coordinate (mm)
        Stabbing_Vel = 5                               % Needle insertion speed (mm/sec)
        omega_max = pi                                 % Maximum rotational velocity (rad/sec)
        max_curvature = 0.0026                         % Maximum curvature for needle control
        k_max                                          % Maximum curvature (computed)
        rot_dir = 1                                    % Rotation direction: CW(1), CCW(-1)
        theta0                                         % Initial theta0 angle
        CM = 1                                         % Control method (0=FF, 1=FB_old, 2=FB_new)
        
        %% ===================================================================
        %  TIMING AND CONTROL PARAMETERS
        %% ===================================================================
        Time_resolution = 0.1                          % Time resolution (sec)
        Time_SimEnd                                    % Simulation end time (sec)
        Epsilon = 0.1                                  % Simulation end distance (mm)
        Freq_ctrl_sec = 0.2                           % Control cycle (sec)
        Freq_ctrl                                      % Control cycle in steps
        Freq_sens_sec = 5                              % Sensing cycle (sec)
        delay_step_sec = 5                             % Sensor delay (sec)
        Freq_sens                                      % Sensing frequency in steps
        Freq_em_sec = 1/10                             % EM sensor frequency (sec)
        
        %% ===================================================================
        %  MOTOR CONTROL PARAMETERS
        %% ===================================================================
        stop_count_insertion = -66647                  % Insertion stop count threshold
        voltage_insertion = 2.2                       % Insertion voltage
        PPR = fix(5000/3)                             % Pulse per revolution
        motor_num_rot = 1                             % Motor number for rotation
        max_error_rot = 0.1                           % Motor control error tolerance (rpm)
        
        %% ===================================================================
        %  SYSTEM FLAGS
        %% ===================================================================
        flag_ekf = 1                                  % Extended Kalman Filter flag
        flag_exp = 1                                  % Experiment flag (1=Experiment, 0=Simulation)
        flag_motor = 1                                % Motor control flag (1=Enable, 0=Disable)
        flag_terminate_z = 0                          % Z-direction termination flag
        flag_terminated = false                       % General termination flag
        
        %% ===================================================================
        %  SIMULATION PARAMETERS
        %% ===================================================================
        scale_model_sim = 1.0                         % Model scaling factor for simulation
        disturbance_sim = [0, 0, 0]                   % Simulated disturbances [x,y,z]
        
        %% ===================================================================
        %  DATA STORAGE ARRAYS
        %% ===================================================================
        Time_Step                                      % Time step array
        Time_num                                       % Number of time steps
        omega_All                                      % Control output history
        Needle_pose_sensor_All                         % Sensor data history
        Needle_pose_act_All                           % Actual needle pose history
        Needle_pose_sensor_realtime_All               % Real-time sensor data history
        Target_Pos_local_All                          % Target position history
        Etc_All                                       % Additional data history
        Needle_pose_All                               % Complete needle pose history
        Mom_Vec_All                                   % Moment vector history
        theta_encoder_All                             % Encoder data history
        Ctrl_Time                                     % Control timing array
        Sensor_Time                                   % Sensor timing array
        data_sensor_All                               % Sensor data cell array
        data_sensor_ctrl_All                          % Control sensor data cell array
        Sensor_Diff_Time                              % Sensor time difference array
        Update_Time                                   % Update timing array
        
        %% ===================================================================
        %  HARDWARE OBJECTS
        %% ===================================================================
        arduino                                       % Arduino communication object
        g                                            % Galil motor control object
        
        %% ===================================================================
        %  TIMER OBJECTS AND CONTROL
        %% ===================================================================
        t_control                                     % Main control timer
        control_Start                                 % Timer start delay
        
        %% ===================================================================
        %  KALMAN FILTER AND STATE ESTIMATION
        %% ===================================================================
        ekf                                          % Extended Kalman filter object
        delay_step_CtrlFreq                          % Sensor delay considering control cycle
        delay_step                                   % Sensor delay step
        
        %% ===================================================================
        %  REAL-TIME CONTROL VARIABLES
        %% ===================================================================
        sensor_flag = false                          % Sensing execution flag
        Step_num = 1                                 % Current step number
        Ctrl_Step_num = 0                            % Control step number
        omega = 0                                    % Current control input (rad/sec)
        Needle_pose                                  % Current needle position
        Needle_pose_delay                            % Delayed needle position
        Needle_pose_sensor                           % Sensor-based needle position
        Needle_pose_sensor_realtime                  % Real-time needle pose
        Needle_pose_act                              % Actual needle pose for control
    end

    methods
        %% ===================================================================
        %  CONSTRUCTOR AND INITIALIZATION
        %% ===================================================================
        function obj = Robot(varargin)
            %ROBOT Constructor for robot class
            %   obj = Robot() - creates robot in normal mode
            %   obj = Robot('simulation', true) - creates robot in simulation mode

            % Parse input arguments
            p = inputParser;
            addParameter(p, 'simulation', false, @islogical);
            parse(p, varargin{:});

            % Set simulation mode
            obj.simulation_mode = p.Results.simulation;

            if obj.simulation_mode
                disp('Robot initialized in SIMULATION MODE - hardware dependencies will be bypassed');
            else
                disp('Robot initialized in NORMAL MODE - hardware dependencies required');
            end
        end

        function obj = startup(obj)
            %STARTUP Initialize robot system and prepare for operation
            obj.current_mode = 'startup';

            %% Initialize computed properties
            obj.theta0 = obj.Needle_pose_ini(6);
            obj.Time_SimEnd = 10 / obj.Stabbing_Vel;
            obj.Freq_ctrl = round(obj.Freq_ctrl_sec / obj.Time_resolution);
            obj.Freq_sens = round(obj.Freq_sens_sec / obj.Time_resolution);
            obj.delay_step_CtrlFreq = round(obj.delay_step_sec / obj.Freq_ctrl_sec);
            obj.control_Start = obj.Time_resolution / 10 * 2;
            obj.delay_step = round(obj.delay_step_sec / obj.Freq_sens_sec);

            %% Initialize target position
            Target_Start = [0, 0, 0];
            obj.Target_Pos_local = Target_Start;

            %% Initialize time and data arrays
            obj.Time_Step = 0:obj.Time_resolution:obj.Time_SimEnd;
            obj.Time_num = numel(obj.Time_Step);
            obj.omega_All = zeros(round(obj.Time_num / obj.Freq_ctrl));
            obj.Needle_pose_sensor_All = zeros(round(obj.Time_num / obj.Freq_sens), 6);
            obj.Needle_pose_act_All = zeros(round(obj.Time_num / obj.Freq_ctrl), 6);
            obj.Needle_pose_sensor_realtime_All = zeros(round(obj.Time_num / obj.Freq_ctrl), 6);
            obj.Target_Pos_local_All = zeros(round(obj.Time_num / obj.Freq_ctrl), 3);
            obj.Etc_All = zeros(round(obj.Time_num / obj.Freq_ctrl), 6);
            obj.Needle_pose_All = zeros(obj.Time_num, 6);
            obj.Mom_Vec_All = zeros(obj.Time_num, 3);
            obj.theta_encoder_All = zeros(round(obj.Time_num / obj.Freq_ctrl), 1);
            obj.k_max = obj.max_curvature;
            obj.Ctrl_Time = zeros(round(obj.Time_num / obj.Freq_ctrl), 1) + obj.Time_SimEnd + 1;
            obj.Sensor_Time = zeros(round(obj.Time_num / obj.Freq_sens), 1) + obj.Time_SimEnd + 1;
            obj.data_sensor_All = cell(round(obj.Time_num / obj.Freq_sens), 1);
            obj.data_sensor_ctrl_All = cell(round(obj.Time_num / obj.Freq_ctrl), 1);
            obj.Sensor_Diff_Time = obj.Sensor_Time;
            obj.Update_Time = zeros(obj.Time_num, 1) + obj.Time_SimEnd + 1;

            %% Initialize needle pose variables
            obj.Needle_pose = obj.Needle_pose_ini;
            obj.Needle_pose_delay = obj.Needle_pose_ini;
            obj.Needle_pose_sensor = obj.Needle_pose_ini;
            obj.Needle_pose_sensor_realtime = obj.Needle_pose_ini;
            obj.Needle_pose_All(1, :) = obj.Needle_pose_ini;

            %% Create Kalman filter object
            obj.ekf = extendedKalmanFilter( ...
                @stateTransitionModel, ...
                @measurementFcn, ...
                obj.Needle_pose_ini);

            %% Timer initialization
            obj.t_control = timer('StartDelay', obj.control_Start, 'Period', obj.Freq_ctrl_sec, 'ExecutionMode', 'fixedRate');
            obj.t_control.TimerFcn = @(~, ~) obj.Control_CB;

            %% Hardware initialization
            if ~obj.simulation_mode
                disp('Setup Start: Motor Control')
                obj.arduino = arduino_comm_init_motor('COM3');
                obj.g = init_galil();
                
                % Access Relay
                obj.g.command('SB 3');
                pause(0.1);
                disp('Relay for drivers should be turned on');
                disp('Setup Terminated: Motor Control')
            else
                disp('SIMULATION MODE: Skipping hardware initialization')
                obj.arduino = [];
                obj.g = [];
                disp('SIMULATION MODE: Hardware objects set to dummy values')
            end
            obj.is_start_up = true;
        end

        %% ===================================================================
        %  ROBOT STATUS AND MODE MANAGEMENT
        %% ===================================================================
        function robot_not_ready = is_startup(obj)
            %IS_STARTUP Check if the robot has been startup properly
            robot_not_ready = ~ obj.is_start_up;
            if robot_not_ready
                disp('Robot is not ready')
            else
                disp('Robot is ready')
            end
        end

        function robot_mode = check_robot_mode(obj)
            %CHECK_ROBOT_MODE Return the current mode of the robot
            robot_mode = obj.current_mode;
        end

        function obj = set_robot_mode(obj, mode)
            %SET_ROBOT_MODE Set robot operation mode
            if ismember(mode, obj.validModes)
                obj.current_mode = mode;
            end
        end

        function is_sim = is_simulation_mode(obj)
            %IS_SIMULATION_MODE Check if robot is in simulation mode
            is_sim = obj.simulation_mode;
        end

        function obj = enable_simulation_mode(obj)
            %ENABLE_SIMULATION_MODE Enable simulation mode
            obj.simulation_mode = true;
            disp('Simulation mode ENABLED - hardware dependencies will be bypassed');
        end

        function obj = disable_simulation_mode(obj)
            %DISABLE_SIMULATION_MODE Disable simulation mode
            obj.simulation_mode = false;
            disp('Simulation mode DISABLED - hardware dependencies required');
            warning('Make sure hardware is properly connected before running startup()');
        end

        %% ===================================================================
        %  COORDINATE TRANSFORMATION AND CALIBRATION
        %% ===================================================================
        function calibration_finsh_flag = calibrate(obj, recieved_matrix)
            %CALIBRATE Calibrate robot with respect to image frame
            origin = obj.registration_matrix;
            obj.registration_matrix = recieved_matrix;
            tolerance = 1e-6;
            calibration_finsh_flag = ~isequal(size(origin), size(obj.registration_matrix)) && ...
                all(abs(origin - obj.registration_matrix) < tolerance, 'all');
        end

        function target_in_robot_frame = target_registration(obj, target)
            %TARGET_REGISTRATION Transform received point to robot frame
            target_in_robot_frame = obj.registration_matrix \ target;
        end

        %% ===================================================================
        %  PLANNING AND TARGET MANAGEMENT
        %% ===================================================================
        function is_reachable = reachable(obj, target)
            %REACHABLE Check if target is reachable by furthest insertion
            is_reachable = true; % No check implemented yet
        end

        function obj = update_target(obj, target)
            %UPDATE_TARGET Update robot target position
            obj.target_position_robot = target;
        end

        function planning_finsh_flag = planning(obj, target)
            %PLANNING Plan path to target
            target_robot = obj.target_registration(target);
            planning_finsh_flag = obj.reachable(target_robot);
        end

        function is_in_workspace = check_target(obj, target)
            %CHECK_TARGET Check if target is in workspace and update if valid
            target_robot = obj.target_registration(target);
            is_in_workspace = obj.reachable(target_robot);

            if is_in_workspace
                obj.update_target(target_robot);
            end
        end

        %% ===================================================================
        %  ROBOT POSE AND POSITION MANAGEMENT
        %% ===================================================================
        function robot_pose = get_robot_current_pose(obj)
            %GET_ROBOT_CURRENT_POSE Return current robot pose in robot coordinate
            robot_pose = obj.Needle_pose_act;
        end

        function obj = set_entry_point(obj, needle_image)
            %SET_ENTRY_POINT Set needle entry point
            current_pos = current_robot_position();
            needle_pos = obj.target_registration(needle_image);
            obj.starting_position = 0.3 .* current_pos + 0.7 .* needle_pos;
        end

        %% ===================================================================
        %  MOVEMENT CONTROL AND EXECUTION
        %% ===================================================================
        function move_to_end(obj)
            %MOVE_TO_END Main insertion function for open loop control
            sim_time = tic;
            start(obj.t_control);

            % Start insertion
            direction = 1;
            voltage = obj.voltage_insertion;

            if ~obj.simulation_mode
                move_insertion(obj.g, direction, voltage);
            else
                disp("SIMULATION MODE: Would start insertion with voltage " + num2str(voltage));
            end

            % Main control loop
            while true
                pause(obj.Time_resolution / 100);
                run_time = toc(sim_time);

                if ~obj.simulation_mode
                    count_current_insertion = record_home_pos(obj.g);
                else
                    count_current_insertion = 1000;
                end

                if count_current_insertion < obj.stop_count_insertion
                    obj.flag_terminate_z = 1;
                end

                if (run_time > obj.Time_SimEnd) || obj.flag_terminate_z == 1
                    obj.flag_terminated = true;
                    break;
                end
            end

            disp('Endpoint satisfied')
            stop(obj.t_control);

            % Stop motors
            if ~obj.simulation_mode
                stop_insertion(obj.g, direction);
            else
                disp("SIMULATION MODE: Would stop insertion with direction " + num2str(direction));
            end

            pause(3);
        end

        function RetractNeedle(obj)
            %RETRACTNEEDLE Retract needle to home position
            disp('homing start')
            threshold = 1000;
            home_pos = 0;

            if ~obj.simulation_mode
                home_insertion(obj.g, home_pos, threshold);
            else
                disp("SIMULATION MODE: Would home insertion with home_pos " + num2str(home_pos) + " and threshold " + num2str(threshold));
            end

            disp('homing done')
        end

        function move_A_step(obj, needle_pos_image)
            %MOVE_A_STEP Move robot one step towards target
            needle_pos_robot = obj.target_registration(needle_pos_image);
            slow_flag = obj.isApprox(needle_pos_robot);
            hit_flag = isInTargetingPos(needle_pos_robot);

            if hit_flag
                obj.RetractNeedle();
            else
                next_step = calculate_next_step(needle_pos_robot, slow_flag);
                move_step(next_step, needle_pos_robot);
            end
        end

        %% ===================================================================
        %  CONTROL CALCULATION FUNCTIONS
        %% ===================================================================
        function next_step = calculate_next_step(obj, needle_pos, slow_flag)
            %CALCULATE_NEXT_STEP Calculate next movement step
            if slow_flag
                next_step = xxxx(needle_pos, obj.target_position_robot, small_step_value);
            else
                next_step = xxxx(needle_pos, obj.target_position_robot, large_step_value);
            end
        end

        function slow_flag = isApprox(obj, needle_pos)
            %ISAPPROX Check if robot is close to target for fine control
            % Implementation pending
            slow_flag = false;
        end

        function hit_flag = isInTargetingPos(obj, needle_pos)
            %ISINTARGETINGPOS Check if robot has reached target position
            current_pos = current_robot_position();
            if obj.target_position_robot - mean(current_pos, needle_pos) < max_error_allowed
                hit_flag = true;
            else
                hit_flag = false;
            end
            obj.update_flag(hit_flag);
        end

        function obj = update_flag(obj, flag)
            %UPDATE_FLAG Update target reached flag
            obj.is_target_reached = flag;
        end

        %% ===================================================================
        %  SIMULATION FUNCTIONS
        %% ===================================================================
        function simulate_needle_movement(obj, time_step)
            %SIMULATE_NEEDLE_MOVEMENT Simulate needle movement for testing
            if ~obj.simulation_mode
                warning('Not in simulation mode. Use enable_simulation_mode() first.');
                return;
            end

            % Simple simulation of needle movement
            insertion_distance = obj.Stabbing_Vel * time_step;
            obj.Needle_pose(3) = obj.Needle_pose(3) + insertion_distance;

            % Simple rotation simulation
            if obj.omega ~= 0
                rotation_angle = obj.omega * time_step;
                obj.Needle_pose(6) = obj.Needle_pose(6) + rotation_angle;
            end

            disp(['SIMULATION: Needle at Z=', num2str(obj.Needle_pose(3)), ...
                      ', Theta=', num2str(obj.Needle_pose(6) * 180 / pi), ' degrees']);
        end

        %% ===================================================================
        %  SYSTEM CONTROL AND SHUTDOWN
        %% ===================================================================
        function obj = stop(obj)
            %STOP Shutdown robot and cleanup resources
            obj.current_mode = 'stop';

            delete(obj.t_control);
            if ~obj.simulation_mode
                disable_galil(obj.g);
                delete(obj.arduino);
            end

            disp("Shutdown completed")
        end

        %% ===================================================================
        %  REAL-TIME CONTROL CALLBACK
        %% ===================================================================
        function Control_CB(obj)
            %CONTROL_CB Main control callback function executed by timer
            
            % Initialize control variables
            omega_temp = obj.omega;
            omega = omega_temp;
            obj.Ctrl_Step_num = obj.Ctrl_Step_num + 1;

            %% State estimation using Kalman filter
            if obj.flag_ekf == 1 && obj.Ctrl_Step_num > 1
                [obj.ekf, Needle_pose_ekf] = Update_EKF(obj.ekf, obj.Needle_pose_sensor, obj.sensor_flag, obj.omega_All, obj.Stabbing_Vel, obj.Freq_ctrl_sec, obj.Ctrl_Step_num, obj.delay_step_CtrlFreq);
                Needle_pose_act = Needle_pose_ekf;
            else
                Needle_pose_act = obj.Needle_pose_sensor;
            end

            obj.sensor_flag = false;

            %% Encoder reading for theta angle
            if ~obj.simulation_mode
                encoder_read = get_encoder_tick(obj.arduino);
                initialPulse = 0;
                theta_encoder = encoder2theta(encoder_read, obj.PPR, initialPulse);
                theta = theta_encoder;
            else
                theta = 0;
                disp(['SIMULATION MODE: Using simulated theta = ', num2str(theta)]);
            end

            % Update needle pose with encoder data
            if ~isprop(obj, 'Needle_pose_sensor_realtime') || isempty(obj.Needle_pose_sensor_realtime)
                obj.Needle_pose_sensor_realtime = obj.Needle_pose_sensor;
            end

            obj.Needle_pose_sensor_realtime(6) = theta;
            Needle_pose_act(6) = theta;

            %% Control algorithm execution
            % Generate needle tip position and transformation matrix
            [P_tb1, T_tb] = Cal_Ptb1_Ttb(Needle_pose_act);

            % Control output calculation
            if (obj.CM == 0 && obj.Ctrl_Step_num == 1) || (obj.CM == 1)
                % Parameter calculation
                [k, P_tt, theta_d] = Cal_k_P_tt_theta_d(obj.Target_Pos_local, T_tb, theta);
                k = abs(k);

                if k > obj.k_max
                    k = obj.k_max;
                end

                % Profile imitation
                [alpha, omega_hat_pro] = Imitation_Profile(k, obj.k_max, theta_d);

                % Update rotation direction
                [obj.rot_dir, obj.theta0] = Update_rot_dir(theta, obj.theta0, obj.rot_dir);

                % Open-loop B-CURV settings
                alpha = 1;
                theta_d = pi;

                % Control output calculation
                omega = Cal_Omega(alpha, theta, theta_d, obj.omega_max, obj.rot_dir);

            elseif obj.CM == 2
                % New feedback control implementation area
            end

            % Store omega value
            obj.omega = omega;

            %% Motor control execution
            omega_rpm = radsec2rpm(omega);
            omega_rpm = 60;
            omega_rpm = fix(omega_rpm);

            disp("Current theta: " + num2str(theta))

            if obj.flag_motor == 1 && ~obj.simulation_mode
                set_rpm_ino(obj.arduino, omega_rpm);
            elseif obj.simulation_mode
                disp(['SIMULATION MODE: Would set motor RPM to ', num2str(omega_rpm), ' [rpm]']);
            end

            %% Data logging
            obj.omega_All(obj.Ctrl_Step_num) = omega;
            obj.Needle_pose_act_All(obj.Ctrl_Step_num, :) = Needle_pose_act;
            obj.Etc_All(obj.Ctrl_Step_num, :) = [theta * 180 / pi, theta_d, omega * 180 / pi, omega_hat_pro * obj.omega_max * 180 / pi, k, alpha];
            obj.theta_encoder_All(obj.Ctrl_Step_num) = theta;
        end
    end
end
