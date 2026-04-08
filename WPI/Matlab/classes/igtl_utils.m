classdef igtl_utils < handle
    %IGTL_UTILS Summary of this class goes here
    %   Detailed explanation goes here

    properties (Access = public)
        host = '127.0.0.1'
        port = 18936
        socket
        status_buffer
        string_buffer
        transformation_buffer
        sender
        receiver
        name
        state
        show_message = true
    end

    methods
        function obj = connect(obj,host,port)
            %connect to igtl server and construct data sender and reciever
            disp("Connecting to IGTL server");
            obj.socket = igtlConnect(host, port);
            obj.receiver = OpenIGTLinkMessageReceiver(obj.socket, @obj.onRxStatusMessage, @obj.onRxStringMessage, @obj.onRxTransformMessage, @onRxPointMessage, @onRxImageMessage);
            obj.sender = OpenIGTLinkMessageSender(obj.socket);
            disp("connect finish");
        end

        function obj = disconnect(obj)
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
            if obj.show_message
                disp(['Received STATUS message ', deblank(deviceName),  text]);
            end
        end
        
        function obj = onRxStringMessage(obj, deviceName, text)
            % Callback when STRING message is received and processed
            % Currently, only prints received value
            obj.string_buffer = text;
            if obj.show_message
                disp(['Received STRING message: ', deblank(deviceName), ' = ', text]);
            end
        end

        function obj = onRxTransformMessage(obj, deviceName, transform)
            % Callback when TRANSFORM message is received and processed
            % Currently, only prints received value
            obj.transformation_buffer = transform;
            if obj.show_message
                disp('Received TRANSFORM message: ');
                disp([deblank(deviceName),  ' = ']);
                disp(transform);
            end
        end
    end
end