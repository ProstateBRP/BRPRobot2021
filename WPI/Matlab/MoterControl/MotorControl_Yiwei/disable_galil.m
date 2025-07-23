function disable_galil(g)    
    % Terminate the Backend Program
    for i = 1:6
        g.command(['CB ', num2str(i)]);
    end

    g.command('OFA=0'); 
    g.command('OFB=0'); 

    delete(g);
    
    disp('Galil Controller Terminated');
end