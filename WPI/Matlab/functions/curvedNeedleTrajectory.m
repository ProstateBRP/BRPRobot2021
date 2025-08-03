function [positions, directions] = curvedNeedleTrajectory(pos_ini, vec_ini, curvature, theta_d, d_space, z_end)
    % Input parameters:
    % pos_ini: Initial position [x, y, z]
    % vec_ini: Initial direction vector (will be normalized)
    % curvature: Scalar curvature value (1/mm)
    % theta_d: Angle defining the plane of curvature (in radians, measured in x-y plane from y-axis CCW)
    % d_space: Spatial resolution for trajectory calculation (mm)
    % z_end: End position in z direction (mm)
    
    % Normalize initial direction vector
    vec_ini = vec_ini / norm(vec_ini);
    
    % Estimate maximum number of points needed
    % Using a conservative estimate based on the z-distance and spatial resolution
    max_points = ceil((z_end - pos_ini(3))/d_space * 2) + 1;  % Factor of 2 for safety
    
    % Initialize arrays for storing positions and directions
    positions = zeros(max_points, 3);
    directions = zeros(max_points, 3);
    
    % Set initial conditions
    positions(1,:) = pos_ini;
    directions(1,:) = vec_ini;
    
    % Create rotation matrix for theta_d in x-y plane
    R_z = [cos(theta_d) -sin(theta_d) 0;
           sin(theta_d) cos(theta_d)  0;
           0           0             1];
    
    % Main calculation loop
    i = 2;
    while i <= max_points && positions(i-1,3) < z_end
        % Current direction
        current_dir = directions(i-1,:);
        
        % Calculate the plane normal vector (rotated based on theta_d)
        base_normal = [0; 1; 0];  % y-axis as reference
        plane_normal = R_z * base_normal;
        
        % Calculate the rotation axis for the curved motion
        rotation_axis = cross(current_dir, plane_normal);
        if norm(rotation_axis) < 1e-10  % Check if vectors are parallel
            rotation_axis = [0 0 1];  % Use z-axis as default (for x-y plane)
        else
            rotation_axis = rotation_axis / norm(rotation_axis);
        end
        
        % Calculate rotation angle based on curvature and spatial step
        angle = -curvature * d_space;
        
        % Create rotation matrix for the incremental step
        rotation_vector = [rotation_axis(:)', angle];
        R = axang2rotm(rotation_vector);
        
        % Update direction
        new_dir = (R * current_dir')';
        new_dir = new_dir / norm(new_dir);
        
        % Update position using direction and spatial step
        positions(i,:) = positions(i-1,:) + d_space * current_dir;
        directions(i,:) = new_dir;
        
        i = i + 1;
    end
    
    % Trim unused points
    positions = positions(1:i-1,:);
    directions = directions(1:i-1,:);
    
    % Adjust final point to exactly match z_end if possible
    if i > 2 && positions(end,3) > z_end
        % Linearly interpolate the final point
        t = (z_end - positions(end-1,3)) / (positions(end,3) - positions(end-1,3));
        final_pos = positions(end-1,:) + t * (positions(end,:) - positions(end-1,:));
        final_dir = directions(end-1,:) + t * (directions(end,:) - directions(end-1,:));
        final_dir = final_dir / norm(final_dir);
        
        positions(end,:) = final_pos;
        directions(end,:) = final_dir;
    end
end