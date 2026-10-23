%% Unit Test: Extended Kalman Filter (EKF) Navigation State Estimation
% Author: Senior Aerospace Engineer
% Verifies sensor fusion, attitude convergence, and gyro bias estimation.

function passed = test_ekf()
    fprintf('[*] Running Test: Multiplicative Extended Kalman Filter (MEKF)...\n');
    passed = true;
    
    params = orion_params();
    
    % True Initial State
    r_true = [params.astro.R_Earth + 185000.0; 0; 0];
    v_true = [0; 7796.0; 0];
    q_true = [1.0; 0.0; 0.0; 0.0];
    bg_true = [0.005; -0.003; 0.002]; % True gyro bias [rad/s]
    
    % Initial Estimate with deliberate errors
    r_est = r_true + [100.0; -50.0; 75.0];
    v_est = v_true + [2.0; -1.5; 1.0];
    q_est = quaternion_utils.from_euler(deg2rad(5.0), deg2rad(-3.0), deg2rad(2.0));
    bg_est = [0.0; 0.0; 0.0]; % Zero initial bias estimate
    
    x0 = [r_est; v_est; q_est; bg_est];
    
    % Initial Covariance P0
    P0 = blkdiag( ...
        (150.0)^2 * eye(3), ... % 150 m position uncertainty
        (5.0)^2 * eye(3),   ... % 5 m/s velocity uncertainty
        (deg2rad(10.0))^2 * eye(3), ... % 10 deg attitude uncertainty
        (0.01)^2 * eye(3)   ... % 0.01 rad/s gyro bias uncertainty
    );

    filter = ekf_estimator(x0, P0, params);
    
    % Simulate 50 seconds of trajectory and sensor updates
    dt = 0.05; % 20 Hz IMU rate
    t_end = 30.0;
    n_steps = floor(t_end / dt);
    
    for i = 1:n_steps
        t = i * dt;
        
        % True angular rate
        omega_true = [0.01 * sin(0.2*t); 0.01 * cos(0.2*t); 0.0];
        dq = quaternion_utils.derivative(q_true, omega_true);
        q_true = quaternion_utils.normalize(q_true + dq * dt);
        
        % Simulated IMU measurements (with bias and Gaussian noise)
        omega_meas = omega_true + bg_true + params.sensors.gyro_noise_std * randn(3, 1);
        a_meas = [0; 0; 0] + params.sensors.accel_noise_std * randn(3, 1);
        
        % 1. Filter Prediction Step (20 Hz)
        filter.predict(a_meas, omega_meas, dt, t);
        
        % 2. Star Tracker Measurement Update (5 Hz)
        if mod(i, 4) == 0
            q_meas_noise = quaternion_utils.from_euler( ...
                params.sensors.star_tracker_noise_std * randn, ...
                params.sensors.star_tracker_noise_std * randn, ...
                params.sensors.star_tracker_noise_std * randn ...
            );
            q_star_meas = quaternion_utils.mult(q_true, q_meas_noise);
            filter.update_star_tracker(q_star_meas);
        end
        
        % 3. Range Measurement Update (1 Hz)
        if mod(i, 20) == 0
            range_meas = norm(r_true) + 5.0 * randn;
            filter.update_range(range_meas);
        end
    end
    
    % Final Error Metrics
    q_est_final = filter.x_hat(7:10);
    q_err = quaternion_utils.error(q_true, q_est_final);
    final_att_err_deg = rad2deg(2.0 * acos(min(1.0, abs(q_err(1)))));
    
    bg_est_final = filter.x_hat(11:13);
    bias_error = norm(bg_est_final - bg_true);
    
    fprintf('    True Gyro Bias          : [%.4f, %.4f, %.4f] rad/s\n', bg_true(1), bg_true(2), bg_true(3));
    fprintf('    Estimated Gyro Bias     : [%.4f, %.4f, %.4f] rad/s\n', bg_est_final(1), bg_est_final(2), bg_est_final(3));
    fprintf('    Residual Gyro Bias Error: %.6f rad/s (Convergence verified)\n', bias_error);
    fprintf('    Final Attitude Error    : %.4f deg (Star Tracker fused)\n', final_att_err_deg);
    
    assert(final_att_err_deg < 0.2, 'Attitude estimation error exceeds 0.2 deg');
    assert(bias_error < 0.002, 'Gyro bias estimation failed to converge');
    
    fprintf('    [PASS] EKF Navigation State Estimation verified.\n');
end
