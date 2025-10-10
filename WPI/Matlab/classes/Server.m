classdef Server < Robot
    %SERVER Summary of this class goes here
    % This class is for communication with upper level control from 3D
    % slicer amd lower level robot hardware. The robot hardware interface
    % is acheieved by constructing "Robot" class.

    
    properties (Access = private)
        host = '127.0.0.1'
        port = 18936
        socket
        status_buffer
        string_buffer
        transformation_buffer
        current_robot_position
        current_needle_position_MRI
        desired_target_location
        open_loop = false
        robot_not_ready
        robot_pose
        robot_mode
        name
        state
        calibration_finsh_flag = false
        planning_finsh_flag = false
        targeting_finsh_flag = false
        target_not_reachable = false
        idle_flag = false
        command_recieved = false
        pool
        sideFuture   % parallel.FevalFuture
        stopSide = true
    end

    properties (Access = public)
        sender
        receiver
        robot
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
            parse(p, varargin{:});
            % Connect to robot control part
            if p.Results.simulation
                obj.simulation_mode = true;
            end
            obj.host = p.Results.host;
            obj.port = p.Results.port;
            obj.open_loop = p.Results.open_loop;
            obj.robot_not_ready = obj.is_startup();

            %obj.robot_pose = obj.robot.get_robot_current_pose();
            % obj.pool = gcp('nocreate'); % get existing pool if any
        end

        function obj = connect(obj)
        %connect to igtl server and construct data sender and reciever
        disp("Connecting to IGTL server");
        obj.socket = igtlConnect(obj.host, obj.port);
        obj.receiver = OpenIGTLinkMessageReceiver(obj.socket, @obj.onRxStatusMessage, @obj.onRxStringMessage, @obj.onRxTransformMessage, @onRxPointMessage, @onRxImageMessage);
        obj.sender = OpenIGTLinkMessageSender(obj.socket);
        disp("connect finish");
        end

        function disconnect(obj)
            msg = "Disconnecting with igtl in 2s";
            obj.sender.WriteOpenIGTLinkStringMessage('DisconnectNotice', msg);
            disp(msg)
            pause(2);
            igtlDisconnect(obj.socket);
            disp("disconnect finish");
        end

        function obj = onRxStatusMessage(obj, deviceName, text)
            % Callback when STATUS message is received and processed
            % Currently, only prints received value
            obj.status_buffer = text;
            disp(['Received STATUS message ', deblank(deviceName),  text]);
        end
        
        function obj = onRxStringMessage(obj, deviceName, text)
            % Callback when STRING message is received and processed
            % Currently, only prints received value
            obj.string_buffer = text;
            disp(['Received STRING message: ', deblank(deviceName), ' = ', text]);
        end

        function obj = onRxTransformMessage(obj, deviceName, transform)
            % Callback when TRANSFORM message is received and processed
            % Currently, only prints received value
            disp('Received TRANSFORM message: ');
            disp([deblank(deviceName),  ' = ']);
            obj.transformation_buffer = transform;
            disp(transform);
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
                    obj.stopSide = false;
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
                                obj.robot_pose = obj.get_robot_current_pose();
                                obj.sender.WriteOpenIGTLinkTransformMessage(char("CURRENT_POSITION"), obj.robot_pose);
                                pause(0.2);
                            else
                                error_message = "Wrong command at this time.";
                                obj.sender.WriteOpenIGTLinkStringMessage(char(obj.state), char(error_message));
                            end
                        elseif strcmpi(type, 'TRANSFORM')
                            obj.sender.WriteOpenIGTLinkTransformMessage(char("ACK_Transform"), data);
                            obj.calibration_finsh_flag = obj.calibrate(data);
                            disp(obj.calibration_finsh_flag)
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
                                obj.robot_pose = obj.get_robot_current_pose();
                                obj.sender.WriteOpenIGTLinkTransformMessage('CURRENT_POSITION', obj.robot_pose);
                            end
                        elseif strcmpi(type, 'TRANSFORM')
                            obj.sender.WriteOpenIGTLinkTransformMessage(char("ACK_Transform"), data);
                            is_in_workspace = obj.check_target(data);
                            disp(is_in_workspace);
                            
                            if ~is_in_workspace
                                status = struct('code', 10, 'subCode', 0, 'errorName', 'Configuration error', 'message', 'STATUS_CONFIG_ERROR');
                                obj.sender.WriteOpenIGTLinkStatusMessage(char(head), status);
                            else
                                status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                                obj.sender.WriteOpenIGTLinkStatusMessage(char(obj.state), status);
                                obj.targeting_finsh_flag = true;
                            end                           
                        else
                            error_message = "Wrong type of message at this time.";
                            obj.sender.WriteOpenIGTLinkStringMessage(char(head), char(error_message));
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
                        disp(data);
                        if strcmpi(data, 'CURRENT_POSITION')
                            obj.robot_pose = obj.get_robot_current_pose();
                            obj.sender.WriteOpenIGTLinkTransformMessage('CURRENT_POSITION', obj.robot_pose);
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
                    final_targeting_reached = false;
                    first_step_flag = true;
                    while ~final_targeting_reached
                        if obj.open_loop
                            % F = parfeval(obj.pool, @robot_postion_server, 0, obj.host, obj.port, obj.Queue);
                            obj.move_to_end();
                            % cancel(F);
                            break
                        else
                            [head, type, data] = obj.receiver.readMessage();
                            if strcmpi(type, 'STRING')
                                if strcmpi(data, 'CURRENT_POSITION')
                                    obj.robot_pose = obj.get_robot_current_pose();
                                    obj.sender.WriteOpenIGTLinkTransformMessage(char("CURRENT_POSITION"), obj.robot_pose);
                                else
                                    error_message = "Wrong command at this time.";
                                    obj.sender.WriteOpenIGTLinkStringMessage(char(head), char(error_message));
                                end
                            elseif strcmpi(type, 'TRANSFORM')
                                obj.sender.WriteOpenIGTLinkStringMessage(char(head), char("ACK_NPSOE"));
                                pause(0.1);
                                if ~is_in_workspace
                                    status = struct('code', 10, 'subCode', 0, 'errorName', 'Configuration error', 'message', 'STATUS_CONFIG_ERROR');
                                    obj.sender.WriteOpenIGTLinkStatusMessage(char(head), status);
                                    break
                                else
                                    if first_step_flag
                                        obj.set_entry_point(data);
                                        first_step_flag = false;
                                    end
                                    status = struct('code', 1, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
                                    obj.sender.WriteOpenIGTLinkStatusMessage(char(head), status);
                                    obj.move_A_step(data);
                                    obj.robot_pose = obj.get_robot_current_pose();
                                    obj.sender.WriteOpenIGTLinkTransformMessage(char(head), obj.robot_pose);
                                    final_targeting_reached = obj.is_target_reached;
                                end                           
                            else
                                error_message = "Wrong type of message at this time.";
                                obj.sender.WriteOpenIGTLinkStringMessage(char(head), char(error_message));
                            end
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
                disp('Already moved');
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
            obj.stopSide = true;     % cooperative stop
            if ~isempty(obj.sideFuture) && ~strcmp(obj.sideFuture.State, 'finished')
                cancel(obj.sideFuture);   % hard stop if needed
            end
            obj.calibration_finsh_flag = false;
            obj.planning_finsh_flag = false;
            obj.targeting_finsh_flag = false;
            obj.target_not_reachable = false;
            delete(gcp('nocreate'));
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
            delete(obj.pool);
        end

        function robot_position_server(obj)
            send(q, "side client started");
            sidesocket = igtlConnect(obj.host, obj.port);
            sidereceiver =OpenIGTLinkMessageReceiver(sidesocket, @obj.onRxStatusMessage, @obj.onRxStringMessage, @obj.onRxTransformMessage, @onRxPointMessage, @onRxImageMessage);
            sidesender = OpenIGTLinkMessageSender(obj.socket);
            while ~obj.stopSide
                [name_local, type, data] = sidereceiver.readCommandMessage();
                if strcmpi(type, 'STRING')
                    if strcmpi(data, 'CURRENT_POSITION')
                        robot_pose_local = obj.get_robot_current_pose();
                        sidesender.WriteOpenIGTLinkTransformMessage(char(name_local), robot_pose_local);
                    elseif strcmpi(data, 'EMERGENCY')
                        obj.onEmergency();
                        obj.stopSide = true;
                        if ~isempty(obj.sideFuture) && ~strcmp(obj.sideFuture.State, 'finished')
                            cancel(obj.sideFuture);   % hard stop if needed
                        end
                    end
                end
            end
            send(q, "side client stopped");
            igtlDisconnect(sidesocket);
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



