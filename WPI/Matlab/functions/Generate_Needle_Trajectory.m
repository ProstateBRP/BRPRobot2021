function trajectory = Generate_Needle_Trajectory(k, theta_d, z_range, initial_pos)
% Generate_Needle_Trajectory  Generate needle trajectory from curvature and target angle
% This is the inverse function of Cal_k_P_tt_theta_d
% 
% input:
%   k           - curvature [1/mm]
%   theta_d     - target angle [rad] (direction in x-y plane)
%   z_range     - z positions [mm] (vector or [z_start, z_end, step])
%   initial_pos - initial position [x, y, z] [mm] (optional, default: [0, 0, 0])
% output:
%   trajectory  - needle trajectory [N x 3] matrix of [x, y, z] positions [mm]

% Handle input arguments
if nargin < 4
    initial_pos = [0, 0, 0];
end

% Parse z_range
if length(z_range) == 3
    % z_range is [z_start, z_end, step]
    z_positions = z_range(1):z_range(3):z_range(2);
else
    % z_range is a vector of z positions
    z_positions = z_range(:)';
end

% Calculate radius from curvature (Paper equation (8) inverse)
if abs(k) < 1e-10
    % Straight line case (zero curvature)
    Radius = inf;
else
    Radius = 1 / abs(k);
end

% Initialize trajectory array
N = length(z_positions);
trajectory = zeros(N, 3);

% Calculate trajectory for each z position
for i = 1:N
    z = z_positions(i) - initial_pos(3); % Relative z position
    
    if Radius == inf
        % Straight line case
        y_rel = 0;
        x_rel = 0;
    else
        % Calculate y from equation (7) inverse
        % Paper equation (7): Radius = y/2 + z^2/(2*y)
        % Rearranging: 2*Radius*y = y^2 + z^2
        % Solving quadratic: y^2 - 2*Radius*y + z^2 = 0
        discriminant = Radius^2 - z^2;
        
        if discriminant < 0
            % No real solution for this z value (z exceeds radius)
            % Use maximum y value (y = Radius when z = 0)
            y_rel = Radius;
        else
            % Two solutions: y = Radius ± sqrt(Radius^2 - z^2)
            % Choose the physically meaningful solution
            % For Cal_k_P_tt_theta_d, P_tt_dash(2) should be positive
            % The solution y = Radius - sqrt(Radius^2 - z^2) gives positive y for small z
            y_rel = Radius - sqrt(discriminant);
            
            % Ensure y is positive and reasonable
            if y_rel < 0 || y_rel > 2*Radius
                y_rel = Radius + sqrt(discriminant);
            end
            
            % Clamp to reasonable range
            if y_rel < 0
                y_rel = 0;
            end
            if y_rel > 2*Radius
                y_rel = 2*Radius;
            end
        end
        
        % x is zero in the rotated frame (circular arc lies in y-z plane)
        x_rel = 0;
    end
    
    % Rotate the y-z plane arc around z by theta_d
    R_z = [cos(theta_d), -sin(theta_d), 0;
           sin(theta_d),  cos(theta_d), 0;
           0,             0,            1];
    
    % Rotate the relative position (in rotated needle tip frame, y-z plane)
    pos_rel_rotated = R_z * [x_rel; y_rel; z];
    
    % Add initial position offset
    trajectory(i, :) = initial_pos + pos_rel_rotated';
end

end
