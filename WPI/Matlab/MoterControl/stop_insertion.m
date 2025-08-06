function stop_insertion(g, direction)
    % direction: 0->pull out, 1->insert

    if (direction == 0)
        g.command('CB 5'); 
    end

    if (direction == 1)
        g.command('CB 4'); 
    end

end