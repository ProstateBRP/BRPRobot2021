function J_B = numericalJacobian_needle_A(omega, Stabbing_Vel, Time_resolution, Needle_pose)
    epsilon = 1e-6; 
    n = numel(omega);
    m = numel(Needle_pose);
    J = zeros(m, n);
    
    u_0 = omega;


    for i = 1:n
        u_1 = u_0;
        
        u_1(i) = u_1(i) + epsilon;

        Needle_pose_partialN

        [f_1,~] = Update_Needle_pose(u_1,Stabbing_Vel,Time_resolution,Needle_pose);
        [f_0,~] = Update_Needle_pose(u_0,Stabbing_Vel,Time_resolution,Needle_pose);

        J_B(:, i) = (f_1 - f_0) / epsilon;
    end
end