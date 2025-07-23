function home_insertion(g, home_pos, threshold)
    current_pos = get_encoder_insertion(g);
    while abs(current_pos - home_pos) > threshold
        voltage = 2;
        direction = 0; % Pull-out
        move_insertion(g, direction, voltage);
        pause(0.1);
        stop_insertion(g, direction);
        current_pos = get_encoder_insertion(g);
    end
end