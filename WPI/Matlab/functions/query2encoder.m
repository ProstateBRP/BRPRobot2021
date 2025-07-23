function encoder_read = query2encoder(arduino)

    message = 'QUERY_ENCODER'; % tentative

    disp(['Sending to Arduino: ', message]);
    writeline(arduino, message);
    
    % Wait briefly for Arduino to respond
    % pause(0.1);
    
    % Read the response (if available)
    if arduino.NumBytesAvailable > 0
        response = readline(arduino);
        disp(['Arduino response: ', response]);
        encoder_read = str2double(response);
    else
        disp('No response from Arduino.');
    end
end



