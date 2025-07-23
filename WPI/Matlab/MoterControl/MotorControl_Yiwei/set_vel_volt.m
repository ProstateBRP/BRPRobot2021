function set_vel_volt(g, motor_num, direction, voltage)
    % motor_num: 3 for Inner, 6 for Outer
    % direction: 0 for CW, 1 for CCW
    % voltage: 0-3.3V

    % Access Relay
    if motor_num ~= 3 && motor_num ~= 6
        disp('Invalid motor number');
        return;
    end

    g.command(['SB ', num2str(motor_num)]);
    disp(['Relay for driver ', num2str(motor_num), ' turned on']);

    % Set Motor Speed
    if motor_num == 3
        g.command(['OFB=', num2str(voltage)]);
        if direction == 0
            % Inner Motor CW
            g.command('SB 2');
        else
            % Inner Motor CCW
            g.command('SB 1');
        end
    elseif motor_num == 6
        g.command(['OFA=', num2str(voltage)]);
        if direction == 0
            % Outer Motor CW
            g.command('SB 4');
        else
            % Outer Motor CCW
            g.command('SB 5');
        end
    end

    disp(['Set Motor ', num2str(motor_num)]);
    disp(['Speed to: ', num2str(voltage), ' V']);
end