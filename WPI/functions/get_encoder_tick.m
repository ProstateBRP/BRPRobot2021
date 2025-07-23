function encoder_read = get_encoder_tick(arduino)
    persistent previous_encoder_read;
    if isempty(previous_encoder_read)
        previous_encoder_read = 0; % Initialize if no previous value exists
    end

    % message = "GET_ENCODER_TICK";
    message = "EC";

    % disp(['Sending to Arduino: ', message]);
    writeline(arduino, message);

    % Wait until data is available
    timeout = 5; % Set a timeout in seconds
    startTime = tic;
    while arduino.NumBytesAvailable == 0
        if toc(startTime) > timeout
            disp('Timeout waiting for response from Arduino.');
            encoder_read = previous_encoder_read; % Return previous value on timeout
            return;
        end
    end

    % Read the response (if available)
    try
        response = readline(arduino);
        % Check if the response is valid
        if isempty(response)
            disp('Empty response from Arduino.');
            encoder_read = previous_encoder_read; % Return previous value on empty response
            return;
        end
    catch ME
        disp(['Error reading response from Arduino: ', ME.message]);
        encoder_read = previous_encoder_read; % Return previous value on read error
        return;
    end

    % disp(['Arduino response: ', response]);

    % Check if the response starts with "EC:"
    if startsWith(response, "EC:")
        % Extract the numeric part after "EC:"
        numericPart = extractAfter(response, "EC:");
        encoder_read = str2double(numericPart);
        if isnan(encoder_read)
            disp('Invalid numeric value in Arduino response.');
            encoder_read = previous_encoder_read; % Return previous value on invalid numeric value
        else
            previous_encoder_read = encoder_read; % Update previous value if valid
        end
    else
        disp(['Unexpected response format from Arduino: ', response]);
        encoder_read = previous_encoder_read; % Return previous value on unexpected format
    end
end
