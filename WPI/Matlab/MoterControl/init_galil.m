function g = init_galil()    
    % Create GalilTools COM server object
    try
        g = actxserver('galil');
    catch
        error('Failed to connect to GalilTools COM server.');
        error('Ensure GalilTools is properly installed.');
    end

    % Get GalilTools library version
    response = g.libraryVersion;
    disp(['Library Version: ', response]);

    % g.address = '';

    % --- MODIFICATION START ---
    % Specify the IP address directly to bypass the connection popup.
    % !!! REPLACE '192.168.1.100' with your controller's actual IP address !!!
    ip_address = '192.168.88.254'; % <-- ★Set your Galil's IP here

    % Use the standard Galil connection string.
    % '-T 1000' sets a 1000ms timeout, which is recommended.
    g.address = ip_address;
    

    disp(['Attempting to connect to: ', g.address]);
    % --- MODIFICATION END ---


    % Get controller model number
    response = g.command(strcat(char(18), char(22)));
    disp(['Connected to: ', response]);

    % Get Serial Number
    response = g.command('MG_BN');
    disp(['Serial Number: ', response]);
    
    % Turn off all digital outputs initially
    % g.command('CB 1,2,3,4,5,6'); % Clear bits 1-6
    for i = 1:6
        g.command(['CB ', num2str(i)]);
    end

    % Initialize motor speeds to 0V for safety
    g.command('OFA=0'); 
    g.command('OFB=0'); 
end