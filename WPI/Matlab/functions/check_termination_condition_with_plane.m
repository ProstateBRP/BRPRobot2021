function is_satisfied = check_termination_condition_with_plane(unit_vector, start_point, distance_to_plane, current_point, tolerance)
    % check_termination_condition_with_plane
    % This function defines a plane perpendicular to a unit vector and checks if a given
    % point satisfies the termination condition based on its distance from the plane.
    %
    % Inputs:
    %   unit_vector       - A unit vector defining the direction of the plane's normal (global coordinate system)
    %   start_point       - Starting point to define the plane's position (global coordinate system)
    %   distance_to_plane - Distance along the unit vector's direction to the plane (local z-axis direction)
    %   current_point     - Current position to evaluate (global coordinate system)
    %   tolerance         - Permissible error margin for determining if the point has reached the plane
    %
    % Output:
    %   is_satisfied      - Logical value indicating if the termination condition is met

    % Step 1: Define a reference point on the plane
    % Compute a point on the plane by moving from the starting point along the unit vector by the specified distance
    plane_point = start_point + distance_to_plane * unit_vector; % Point on the plane

    % Step 2: Specify the plane's normal vector
    % The plane's normal vector is the same as the unit vector provided
    plane_normal = unit_vector; % Normal vector to the plane

    % Step 3: Compute the vector from the current point to the reference point on the plane
    % This helps in determining the relative position of the current point to the plane
    vector_to_plane = current_point - plane_point; % Vector from current point to plane reference point

    % Step 4: Project the vector onto the normal to calculate the signed distance
    % Use the dot product to project the vector onto the plane's normal
    projected_distance = dot(vector_to_plane, plane_normal); % Signed distance from the plane

    % Step 5: Check if the absolute projected distance is within the specified tolerance
    % If the absolute distance is less than or equal to the tolerance, the termination condition is met
    is_satisfied = abs(projected_distance) <= tolerance; % Logical output

    is_satisfied = projected_distance >= 0;

    % test
    projected_distance
end
