function set_rpm_ino(arduino, rpm)
    % if rpm == 0
        % message = "STOP";
        % disp("Stop Rotation")
    % else
        % Send a string to Arduino
        message = strcat("SET_RPM_", num2str(rpm));
    % end

    % disp(['Sending to Arduino: ', message]);
    writeline(arduino, message);
    
    % Wait briefly for Arduino to respond
    % pause(0.1);
    
    % Read the response (if available)
    if arduino.NumBytesAvailable > 0
        response = readline(arduino);
        % disp(['Arduino response: ', response]);
    else
        % disp('No response from Arduino.');
    end
end



