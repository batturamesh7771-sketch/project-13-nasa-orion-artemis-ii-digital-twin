%% Unit Test: Closed-Loop Quaternion Attitude Controller
% Author: Senior Aerospace Engineer
% Verifies pointing stabilization from 45 deg error within <0.1 deg residual error.

function passed = test_attitude_control()
    fprintf('[*] Running Test: Closed-Loop Attitude Control...\n');
    passed = true;
    
    params = orion_params();
    J = params.orbital.inertia;
    
    % Target: Inertial aligned [1; 0; 0; 0]
    q_target = [1.0; 0.0; 0.0; 0.0];
    omega_target = [0.0; 0.0; 0.0];
    
    % Initial condition: 45 degree tilt error about Y axis, zero rate
    q0 = quaternion_utils.from_euler(0.0, deg2rad(45.0), 0.0);
    omega0 = [0.0; 0.0; 0.0];
    
    % Simulation loop (80 seconds at dt = 0.05 s)
    dt = 0.05;
    t_end = 80.0;
    n_steps = floor(t_end / dt);
    
    q_cur = q0;
    omega_cur = omega0;
    
    for i = 1:n_steps
        % Compute control torque
        tau_cmd = attitude_controller(q_target, q_cur, omega_cur, omega_target, params);
        
        % RK4 integration of attitude dynamics
        k1 = attitude_dynamics(0, [q_cur; omega_cur], tau_cmd, J);
        k2 = attitude_dynamics(0, [q_cur; omega_cur] + 0.5 * dt * k1, tau_cmd, J);
        k3 = attitude_dynamics(0, [q_cur; omega_cur] + 0.5 * dt * k2, tau_cmd, J);
        k4 = attitude_dynamics(0, [q_cur; omega_cur] + dt * k3, tau_cmd, J);
        
        state_next = [q_cur; omega_cur] + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4);
        q_cur = quaternion_utils.normalize(state_next(1:4));
        omega_cur = state_next(5:7);
    end
    
    % Final pointing error
    q_final_err = quaternion_utils.error(q_target, q_cur);
    final_angle_deg = rad2deg(2.0 * acos(min(1.0, abs(q_final_err(1)))));
    final_rate_deg_s = rad2deg(norm(omega_cur));
    
    fprintf('    Initial Attitude Error : 45.00 deg\n');
    fprintf('    Final Attitude Error   : %.4f deg (Spec < 0.1 deg)\n', final_angle_deg);
    fprintf('    Final Angular Rate     : %.4f deg/s (Spec < 0.01 deg/s)\n', final_rate_deg_s);
    
    assert(final_angle_deg < 0.1, 'Attitude pointing error exceeds 0.1 deg limit');
    assert(final_rate_deg_s < 0.01, 'Attitude rate exceeds 0.01 deg/s limit');
    
    fprintf('    [PASS] Attitude Controller stabilization verified.\n');
end
