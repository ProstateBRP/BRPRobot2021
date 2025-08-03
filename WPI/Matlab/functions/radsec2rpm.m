function rpm = radsec2rpm(rad_per_sec)
    % RADSEC_TO_RPM Converts angular velocity from rad/s to rpm
    % 
    %   rpm = RADSEC_TO_RPM(rad_per_sec)
    %   Converts the input angular velocity in radians per second (rad/s)
    %   to revolutions per minute (rpm).
    %
    % Input:
    %   rad_per_sec - Angular velocity in radians per second
    %
    % Output:
    %   rpm - Angular velocity in revolutions per minute

    % Conversion factor: 1 rad/s = 60 / (2 * pi) rpm
    conversion_factor = 60 / (2 * pi);

    % Perform conversion
    rpm = rad_per_sec * conversion_factor;
end
