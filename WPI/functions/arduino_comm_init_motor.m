function arduino = arduino_comm_init_motor(port)
    % Define the COM port and baud rate
    baudRate = 115200;
    

    % Create a serialport object
    arduino = serialport(port, baudRate);
    
    % Configure timeout and terminator (optional)
    configureTerminator(arduino, "LF");
    arduino.Timeout = 10;  % Timeout in seconds
    
    % Wait for Arduino's "ready" message
    pause(2);  % Allow Arduino to reset and send initial message
    if arduino.NumBytesAvailable > 0
        readyMessage = readline(arduino);
        disp(['Arduino says: ', readyMessage]);
    end
end