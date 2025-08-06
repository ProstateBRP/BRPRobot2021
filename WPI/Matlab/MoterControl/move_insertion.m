function move_insertion(g, direction, voltage)
    % direction: 0->pull out, 1->insert

    g.command(['OFB=', num2str(voltage)]);
    % disp(['Set Insertion Motor Voltage to: ', num2str(voltage), ' V']);

    if (direction == 0)
        g.command('SB 5'); 
    end

    if (direction == 1)
        g.command('SB 4'); 
    end
        
end