function J_A = numericalJacobian_needle_A(omega, Stabbing_Vel, Time_resolution, Needle_pose)
    epsilon = 1e-6; 
    n = numel(Needle_pose);
    m = numel(Needle_pose);
    J = zeros(m, n);
    
    x_0 = Needle_pose;


    for i = 1:n
        x_1 = x_0;
        
        x_1(i) = x_1(i) + epsilon;

        Needle_pose_partialN

        [f_1,~] = Update_Needle_pose(omega,Stabbing_Vel,Time_resolution,x_1);
        [f_0,~] = Update_Needle_pose(omega,Stabbing_Vel,Time_resolution,x_0);

        J_A(:, i) = (f_1 - f_0) / epsilon;
    end
end