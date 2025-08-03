function theta = encoder2theta(encoderReading, countsPerRevolution, initialCount)
    % Convert encoder reading to theta in radians considering an initial count
    %
    % Parameters:
    %   encoderReading - The reading from the encoder
    %   countsPerRevolution - The number of counts per full revolution of the encoder
    %   initialCount - The initial count to be considered
    %
    % Returns:
    %   theta - The angle in radians

    % gear_ratio = 3;
    % gear_ratio = 2.0;

    % Calculate theta in radians considering the initial count
    theta = (encoderReading - initialCount) / (countsPerRevolution) * 2 * pi;
    theta = theta; % Flip sign to align with coordinate
end