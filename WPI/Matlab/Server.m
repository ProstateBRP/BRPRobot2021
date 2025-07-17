classdef Server < handle
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
    end

    properties (Access = public)
        sender
        receiver
        robot
        validCommands = ["START_UP", "CALIBRATION", "PLANNING", "TARGETING",...
                         "IDLE", "MOVE_TO_TARGET", "STOP"];
    end
    
    methods
        function obj = Server(varargin)
            %SERVER Construct an instance of this class
            %   Detailed explanation goes here
            p = inputParser;
            addParameter(p, 'host', obj.host);
            addParameter(p, 'port', obj.port);
            addParameter(p, 'simulation', false, @islogical);
            parse(p, varargin{:});
            % Connect to robot control part
            if p.Results.simulation
                obj.robot = Robot('simulation', true);
            else
                obj.robot = robot();
            end
            obj.host = p.Results.host;
            obj.port = p.Results.port;
        end

        function obj = connect(obj)
        %connect to igtl server and construct data sender and reciever
        disp("Connecting to IGTL server");
        obj.socket = igtlConnect(obj.host, obj.port);
        obj.receiver = OpenIGTLinkMessageReceiver(obj.socket, @onRxStatusMessage, @obj.onRxStringMessage, @obj.onRxTransformMessage, @onRxPointMessage, @onRxImageMessage);
        obj.sender = OpenIGTLinkMessageSender(obj.socket);
        disp("connect finish");
        obj.sender.WriteOpenIGTLinkStringMessage('Connection Notice', 'IGTL connected');
        msg = 'Ready to take commands, please start the robot first.';
        obj.sender.WriteOpenIGTLinkStringMessage('Connection Notice', msg);
        end

        function disconnect(obj)
            msg = "Disconnecting with igtl in 2s";
            obj.sender.WriteOpenIGTLinkStringMessage('DisconnectNotice', msg);
            disp(msg)
            pause(2);
            igtlDisconnect(obj.socket);
            disp("disconnect finish");
        end
        
        function robot_postion_server(obj)
            %if having any socket function issue, define a new socket here
            while true
                [name, type, data] = obj.receiver.readMessage();
                if strcmpi(type, 'STRING')
                    if strcmpi(data, 'GET_TRANSFORM')
                        % robot_pose = obj.robot.get_robot_current_pose();
                        obj.sender.WriteOpenIGTLinkTransformMessage(char(name), robot_pose);
                        pause(0.2);
                    else
                        error_message = "Wrong command at this time.";
                        obj.sender.WriteOpenIGTLinkStringMessage(char(name), char(error_message));
                    end
                else
                    error_message = "Wrong type of message at this time.";
                    obj.sender.WriteOpenIGTLinkStringMessage(char(name), char(error_message));
                end
            end
        end

        % function obj = onRxStatusMessage(obj, deviceName, text)
        %     % Callback when STATUS message is received and processed
        %     % Currently, only prints received value
        %     obj.status_buffer = text;
        %     disp(['Received STATUS message ', deblank(deviceName),  text]);
        % end
        
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

    end
end

