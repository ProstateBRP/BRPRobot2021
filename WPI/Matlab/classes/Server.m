classdef Server < Robot
    %SERVER Summary of this class goes here
    % This class is for communication with upper level control from 3D
    % slicer amd lower level robot hardware. The robot hardware interface
    % is acheieved by constructing "Robot" class.

    
    properties (Access = private)
        current_robot_position
        current_needle_position_MRI
        desired_target_location
        robot_not_ready
        robot_mode
        calibration_finsh_flag = false
        planning_finsh_flag = false
        targeting_finsh_flag = false
        target_not_reachable = false
        idle_flag = false
        command_recieved = false
        PyReady = false
        SrcDir
        PyDir
        exsi = false
        autoNeedle = false
        VenvPython
        Hostname = "10.0.1.1"
    end

    properties (Access = public)
        validCommands = ["START_UP", "CALIBRATION", "PLANNING", "TARGETING",...
                         "IDLE", "MOVE_TO_TARGET", "STOP", "EMERGENCY", "RETRACT_NEEDLE"];
    end
    
    methods
        function obj = Server(varargin)
            %SERVER Construct an instance of this class
            %   Detailed explanation goes here
            p = inputParser;
            addParameter(p, 'host', obj.host);
            addParameter(p, 'port', obj.port);
            addParameter(p, 'open_loop', obj.open_loop);
            addParameter(p, 'simulation', false, @islogical);
            addParameter(p, 'exsi', obj.exsi);
            addParameter(p, 'auto', obj.autoNeedle);
            addParameter(p, 'show_message', obj.show_message);
            parse(p, varargin{:});
            % Connect to robot control part
            if p.Results.simulation
                obj.simulation_mode = true;
            end
            obj.host = p.Results.host;
            obj.port = p.Results.port;
            obj.socket = obj.connect(obj.host,obj.port);
            obj.open_loop = p.Results.open_loop;
            obj.exsi = p.Results.exsi;
            obj.autoNeedle = p.Results.auto;
            obj.show_message = p.Results.show_message;
            obj.robot_not_ready = obj.is_startup();
            if obj.exsi
                obj.connect_exsi();
            end
        end

        function obj = connect_exsi(obj)
            % Locate project folders (cross-platform safe)
            thisFile = mfilename("fullpath");      % .../src/classes/Server.m
            classDir = fileparts(thisFile);        % .../src/classes
            srcDir   = fileparts(classDir);        % .../src
            exsiDir  = fullfile(srcDir, "exsi_cmds");

            if ispc
                venvPython = fullfile(exsiDir, "venv", "Scripts", "python.exe");
            else
                venvPython = fullfile(exsiDir, "venv", "bin", "python");
            end

            if ~isfile(venvPython)
                error("Python venv not found at: %s", venvPython);
            end

            try
                terminate(pyenv);
            catch
            end

            pe = pyenv("Version", venvPython);
            disp(pe);

            if count(string(py.sys.path), string(srcDir)) == 0
                insert(py.sys.path, int32(0), srcDir);
            end

            py.importlib.import_module("exsi_cmds.matlab_bridge");
            py.exsi_cmds.matlab_bridge.init(obj.Hostname);
            obj.PyReady = true;
            fprintf("Python + ExSi bridge initialized successfully.\n");
        end

        function scan_once(obj)
            obj.assert_exsi_ready();
            task_list = int64(cellfun(@double, cell(py.exsi_cmds.matlab_bridge.get_task_list())));
            sag_id = string(task_list(end-1));
            cor_id = string(task_list(end));
            py.exsi_cmds.matlab_bridge.select_task(sag_id)
            disp("Wait to active task")
            pause(4);
            while true
                state = int64(py.exsi_cmds.matlab_bridge.get_state());
                if state == 0
                    py.exsi_cmds.matlab_bridge.start_scan();
                    break
                else
                    pause(0.1);
                end
            end  
            while true
                state = int64(py.exsi_cmds.matlab_bridge.get_state());
                if state == 0
                    break
                else
                    pause(0.1);
                end
            end
            py.exsi_cmds.matlab_bridge.select_task(cor_id)
            disp("Wait to active task")
            pause(4);
            while true
                state = int64(py.exsi_cmds.matlab_bridge.get_state());
                if state == 0
                    py.exsi_cmds.matlab_bridge.start_scan();
                    break
                else
                    pause(0.1);
                end
            end 
        end

        function adjust_scan_plane(obj, current)
            obj.assert_exsi_ready();
            task_list = int64(cellfun(@double, cell(py.exsi_cmds.matlab_bridge.get_task_list())));
            sag_id = string(task_list(end-1));
            cor_id = string(task_list(end));
            py.exsi_cmds.matlab_bridge.select_task(sag_id, pyargs('activate', logical(false)));
            pause(1);
            py.exsi_cmds.matlab_bridge.set_rx_geometry('sagittal',string(current(1)-0.5),string(current(1)+0.5))
            py.exsi_cmds.matlab_bridge.select_task(cor_id, pyargs('activate', logical(false)));
            pause(1);
            py.exsi_cmds.matlab_bridge.set_rx_geometry('sagittal',string(current(2)-0.5),string(current(2)+0.5))
        end

        function assert_exsi_ready(obj)
            if ~obj.PyReady
                error("Python bridge not initialized. Call connect_exsi first.");
            end
        end

        function obj = onStartUp(obj)
            disp('Start_up');
            id = split(obj.name, '_');
            obj.sender.WriteOpenIGTLinkStringMessage(char("ACK_"+id(2)), char(obj.state));
            if obj.robot_not_ready
                % Start up the robot
                obj.startup();
                obj.robot_not_ready = obj.is_startup();
                %if it's started or not, wait for it to start up
                if obj.robot_not_ready
                    status = struct('code', 13, 'subCode', 13, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                    error_message = "Start up fail, check robot status";
                    disp(error_message)
                else
                    status = struct('code', 1, 'subCode', 1, 'errorName', 'none', 'message', 'STATUS_OK');
                    obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                    status = struct('code', 1, 'subCode', 1, 'errorName', 'none', 'message', 'STATUS_OK');
                    obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
                    % obj.sideFuture = parfeval(backgroundPool, @Server.robot_position_server, 0, obj);
                    obj.idle_flag = true;
                    obj.state = "IDLE";        
                    obj.set_robot_mode('idle');
                end
            end
            if obj.command_recieved
                disp('Already started up');
                obj.command_recieved = false;
            end                           
        end
        
        function obj = onCalibration(obj)
            
            if obj.calibration_finsh_flag
                disp("Redo Calibration");
                obj.calibration_finsh_flag = false;
            else
                disp('Calibration');
            end
            %First Check if robot has started up
            fail_flag = false;
            id = split(obj.name, '_');
            obj.robot_mode = obj.check_robot_mode();
            if ~obj.robot_not_ready 
                obj.sender.WriteOpenIGTLinkStringMessage(char("ACK_"+id(2)), char(obj.state));
                % Set the robot into calibration mode
                if ~strcmp(obj.robot_mode, 'calibration')
                    %try to set the robot mode in calibration
                    obj.set_robot_mode('calibration');
                    obj.robot_mode = obj.check_robot_mode();               
                    if ~strcmp(obj.robot_mode, 'calibration')
                        status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                        error_message = "Start Calibration fail, check robot status, back to IDLE.";
                        disp(error_message);
                        fail_flag = true;
                    else
                        status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                    end
                    obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                end
                if ~fail_flag
                    while ~obj.calibration_finsh_flag
                        [~, type, data] = obj.receiver.readMessage();
                        if strcmpi(type, 'STRING')
                            if strcmpi(data, 'CURRENT_POSITION')
                                obj.Send_Current_Position();
                            else
                                error_message = "Wrong command at this time.";
                                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.state), char(error_message));
                            end
                        elseif strcmpi(type, 'TRANSFORM')
                            obj.sender.WriteOpenIGTLinkTransformMessage(char("ACK_Transform"), data);
                            obj.calibration_finsh_flag = obj.calibrate(data);
                            % disp(obj.calibration_finsh_flag)
                            if ~obj.calibration_finsh_flag
                                status = struct('code', 10, 'subCode', 0, 'errorName', 'Configuration error', 'message', 'STATUS_CONFIG_ERROR');
                                break
                            else
                                status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                                obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                            end
                            status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                            obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status); 
                        else
                            error_message = "Wrong command at this time.";
                        end
                    end
                end
            else
                error_message = 'Robot not start up, intialize the robot first!';
                disp(error_message);
                % server.sender.WriteOpenIGTLinkStringMessage(char(name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
            end
            if obj.command_recieved
                disp('Calibration finished');
                obj.command_recieved = false;
                obj.idle_flag = true;
                obj.state = "IDLE";        
                obj.set_robot_mode('idle');
            end                           
        end
        
        function obj = onPlanning(obj)
            if obj.planning_finsh_flag
                disp("Redo planning");
                obj.planning_finsh_flag = false;
            else
                disp('Planning');
            end
            fail_flag = false;
            id = split(obj.name, '_');
            if ~obj.robot_not_ready && obj.calibration_finsh_flag
                obj.sender.WriteOpenIGTLinkStringMessage(char("ACK_"+id(2)), char(obj.state));
                % Set the robot into planning mode
                if ~strcmp(obj.robot_mode, 'planning')
                    obj.set_robot_mode('planning');
                    obj.robot_mode = obj.check_robot_mode();
                    
                    if ~strcmp(obj.robot_mode, 'planning')
                        status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                        obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
                        error_message = "Start planning fail, check robot status";
                        disp(error_message);
                        fail_flag = true;
                    end
                end
                if ~fail_flag
                    obj.planning_finsh_flag = true;
                    status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                    obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                end
            %Get into calibration without starting the robot
            elseif obj.robot_not_ready
                error_message = 'Robot not start up, intialize the robot first!';
                disp(error_message);
                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
            elseif ~obj.calibration_finsh_flag
                error_message = 'Robot not calibrated, calibrate the robot first!';
                disp(error_message);
                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
            end
            if obj.command_recieved
                disp('Already planned');
                obj.idle_flag = true;
                obj.state = "IDLE";
                obj.command_recieved = false;
                obj.set_robot_mode('idle');
            end
        end    
        
        function obj = onTargeting(obj)
            if obj.targeting_finsh_flag
                disp('Redo Targeting');
                obj.targeting_finsh_flag = false;
            else
                disp('Targeting');
            end
            fail_flag = false;
            id = split(obj.name, '_');
            if ~obj.robot_not_ready && obj.planning_finsh_flag
                obj.sender.WriteOpenIGTLinkStringMessage(char("ACK_"+id(2)), char(obj.state));
                % Set the robot into targeting mode
                if ~strcmp(obj.robot_mode, 'targeting')
                    obj.set_robot_mode('targeting');
                    obj.robot_mode = obj.check_robot_mode();
                    
                    if ~strcmp(obj.robot_mode, 'targeting')
                        status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                        error_message = "Start targeting fail, check robot status";
                        disp(error_message);
                        fail_flag = true;
                    else
                        status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                    end
                    obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                    obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
                end
                % If succesfully set mode, satrt to listen to target
                if ~fail_flag
                    while ~obj.targeting_finsh_flag
                        [head, type, data] = obj.receiver.readMessage();
                        if strcmpi(type, 'STRING')
                            if strcmpi(data, 'CURRENT_POSITION')
                                obj.Send_Current_Position();
                            end
                        elseif strcmpi(type, 'TRANSFORM')
                            obj.sender.WriteOpenIGTLinkTransformMessage(char("ACK_Transform"), data);
                            is_in_workspace = obj.check_target(data);
                            disp(is_in_workspace);
                            
                            if ~is_in_workspace
                                status = struct('code', 10, 'subCode', 0, 'errorName', 'Configuration error', 'message', 'STATUS_CONFIG_ERROR');
                                obj.sender.WriteOpenIGTLinkStatusMessage(char(head), status);
                                break
                            else
                                status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
                                obj.targeting_finsh_flag = true;
                            end                           
                        else
                            error_message = "Wrong type of message at this time.";
                            obj.sender.WriteOpenIGTLinkStringMessage(char(head), char(error_message));
                            break
                        end
                    end
                end
            %Get into calibration without starting the robot
            elseif obj.robot_not_ready
                error_message = 'Robot not start up, intialize the robot first!';
                disp(error_message);
                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
            elseif ~obj.planning_finsh_flag
                error_message = 'Target not planed, plan the target first!';
                disp(error_message);
                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
            end
            if obj.command_recieved
                disp('Already targeted');
                obj.idle_flag = true;
                obj.state = "IDLE";
                obj.command_recieved = false;
                obj.set_robot_mode('idle');
            end
        end

        function obj = onIdle(obj)
            if ~obj.robot_not_ready
                disp('Idle');
                while obj.idle_flag
                    [obj.name, type, data] = obj.receiver.readMessage();
                    if strcmpi(type, 'STRING')
                        %disp(data);
                        if strcmpi(data, 'CURRENT_POSITION')
                            obj.Send_Current_Position();
                        elseif ismember(data, obj.validCommands)
                            msg = "Exiting idle mode, and getting into " + data + " mode.";
                            disp(msg);
                            obj.idle_flag = false;
                            obj.command_recieved = true;
                            obj.state = data;
                        else
                            error_message = "Unknown Command, Please check.";
                            disp(error_message);
                        end
                    else
                        error_message = "Wrong command at this time.";
                        disp(error_message);
                    end
                end
            else
                error_message = 'Robot not start up, intialize the robot first!';
                disp(error_message);
                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
                obj.idle_flag = false;
                obj.command_recieved = false;
           end
        end

        function obj = onMove(obj)
            disp('Scan & Move');
            pause(0.5)
            final_targeting_reached = false;
            fail_flag = false;
            id = split(obj.name, '_');
            if ~obj.robot_not_ready && obj.targeting_finsh_flag
                obj.sender.WriteOpenIGTLinkStringMessage(char("ACK_"+id(2)), char(obj.state));
                % Set the robot into calibration mode
                if ~strcmp(obj.robot_mode, 'move_to_goal')
                    obj.set_robot_mode('move_to_goal');
                    obj.robot_mode = obj.check_robot_mode();
                    
                    if ~strcmp(obj.robot_mode, 'move_to_goal')
                        status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                        error_message = "Start moving fail, check robot status";
                        disp(error_message);
                        fail_flag = true;
                    else
                        status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                    end
                    obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                    
                end
                if ~fail_flag
                    if obj.open_loop
                        final_targeting_reached = obj.move_to_end();
                        while obj.flag_terminate_z ~= 1
                            [~, ~, data] = obj.receiver.readCommandMessage();
                            if data == "STOP" 
                                obj.onStop()
                                obj.flag_terminate_z = 1;
                                delete_all
                            elseif data == "EMERGENCY"
                                obj.onEmergency()
                                obj.flag_terminate_z = 1;
                                delete_all
                            end
                        end
                    else
                        i = 1;
                        while i <= numel(obj.trajectory)
                            % With MRI feedback would be look like below
                            obj.current_Z_target = obj.trajectory(i);
                            obj.theta0 = obj.zRotation;
                            disp("Current Target:")
                            disp(obj.target_relative_global)
                            if obj.exsi
                                obj.scan_once();
                            end
                            if obj.autoNeedle
                                [head, ~, data] = obj.receiver.readTransformationMessage();
                                if strcmpi(head, 'CurrentTrackedTip')
                                    obj.sender.WriteOpenIGTLinkStringMessage(char(head), char("ACK_NPSOE"));
                                    pause(0.01);
                                    current = data(1:3,4);
                                else
                                    error_message = "Wrong message header.";
                                    obj.sender.WriteOpenIGTLinkStringMessage(char(head), char(error_message));
                                end
                            else
                                user_input = input('Enter a 1x3 matrix like [1,2,3]: ', 's');
                                current = transpose(str2num(user_input));      
                            end
                            obj.target_relative_global = obj.target_position_image(1:3,4) - current;
                            if obj.exsi
                                obj.adjust_scan_plane(current);
                            end
                            disp('Relative target')
                            disp(obj.target_relative_global)
                            disp('Mid_steps')
                            disp(obj.trajectory)
                            disp("current target")
                            disp(obj.current_Z_target)
                            disp('Press Enter to continue...');
                            input('', 's');
                            final_targeting_reached = obj.move_to_end();
                            while obj.flag_terminate_z ~= 1
                                [~, ~, data] = obj.receiver.readCommandMessage();
                                if data == "STOP" 
                                    obj.onStop()
                                    obj.flag_terminate_z = 1;
                                    delete_all
                                elseif data == "EMERGENCY"
                                    obj.onEmergency()
                                    obj.flag_terminate_z = 1;
                                    delete_all
                                end
                            end
                            i = i+1;
                        end
                    end
                    obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
                    if final_targeting_reached
                        msg = "Reached Final target.";
                    else
                        msg = "Target not reachable anymore.";
                    end
                    disp(msg)
                    %Get into calibration without starting the robot
                elseif obj.robot_not_ready
                    error_message = 'Robot not start up, intialize the robot first!';
                    disp(error_message);
                    obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                    status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                    obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
                elseif ~obj.calibration_finsh_flag
                    error_message = 'Robot not calibrated, calibrate the robot first!';
                    disp(error_message);
                    obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                    status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                    obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
                elseif ~obj.targeting_finsh_flag
                    error_message = 'No target recieved, finish targeting the robot first!';
                    disp(error_message);
                    obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                    status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                    obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
                end
                if obj.command_recieved
                    disp('Already moved');
                    obj.idle_flag = true;
                    obj.state = "IDLE";
                    obj.command_recieved = false;
                    obj.set_robot_mode('idle');
                end
            end
        end

        function obj = onRetractNeedle(obj)
            disp("Retract needle to home pose")
            % fail_flag = false;
            id = split(obj.name, '_');
            if ~obj.robot_not_ready
                obj.sender.WriteOpenIGTLinkStringMessage(char("ACK_"+id(2)), char(obj.state));
                status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                obj.sender.WriteOpenIGTLinkStatusMessage(char("CURRENT_STATUS"), status);
                obj.RetractNeedle();
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
            else
                error_message = 'Robot not start up, intialize the robot first!';
                disp(error_message);
                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.name), error_message);
                status = struct('code', 13, 'subCode', 0, 'errorName', 'Device not ready', 'message', 'STATUS_NOT_READY');
                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.name), status);
            end
            if obj.command_recieved
                disp('Already Retracted');
                obj.idle_flag = true;
                obj.state = "IDLE";
                obj.command_recieved = false;
                obj.set_robot_mode('idle');
            end
        end
        
        function obj = onStop(obj)
            disp("Stop the robot and communication");
            obj.stop();
            obj.robot_not_ready = true;
            obj.idle_flag = false;
            obj.state = "STOP";
            obj.command_recieved = false;
            obj.set_robot_mode('stop');
            obj.calibration_finsh_flag = false;
            obj.planning_finsh_flag = false;
            obj.targeting_finsh_flag = false;
            obj.target_not_reachable = false;
            if obj.exsi
                obj.stop_master();
            end
            delete all
        end

        function obj = onEmergency(obj)
            disp("EMERGENCY STOP!");
            obj.Emergency();
            obj.robot_not_ready = true;
            obj.idle_flag = false;
            obj.state = "STOP";
            obj.command_recieved = false;
            obj.set_robot_mode('stop');
        end

        function obj = Run(obj)
            % The main running loop for the system
            while true
                if ~obj.idle_flag && ~obj.command_recieved
                    [obj.name, obj.state] = obj.receiver.readCommandMessage();
                end
                switch obj.state
                    case "START_UP"
                        obj.onStartUp();
                    case "CALIBRATION"
                        obj.onCalibration();
                    case "PLANNING"
                        obj.onPlanning();
                    case "TARGETING"
                        obj.onTargeting();
                    case "IDLE"
                        obj.onIdle();
                    case "MOVE_TO_TARGET"
                        obj.onMove();
                    case "RETRACT_NEEDLE"
                        obj.onRetractNeedle();                   
                    case "STOP"
                        obj.onStop();
                        break
                    case "EMERGENCY"
                        obj.onEmergency();
                end
            end
            disp("Main Loop Exited")
        end

    end

end



