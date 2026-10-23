%% Multiplicative Extended Kalman Filter (MEKF) for Orion Navigation
% Author: Senior Aerospace Engineer
% Aerospace-standard MEKF for 6-DOF state estimation:
%   - States: Position (3), Velocity (3), Attitude Quaternion (4), Gyro Bias (3)
%   - Error State: [delta_r(3); delta_v(3); delta_theta(3); delta_bg(3)] (12x1)
%   - Fuses IMU gyros & accelerometers with Star Tracker attitude and Range measurements.

classdef ekf_estimator < handle
    properties
        x_hat           % Estimated state [r(3); v(3); q(4); bg(3)] (13x1)
        P               % Error state covariance matrix (12x12)
        Q               % Process noise covariance (12x12)
        R_star          % Star tracker measurement covariance (3x3)
        R_range         % Range measurement covariance (1x1)
        params          % Spacecraft parameters
    end
    
    methods
        %% Constructor
        function obj = ekf_estimator(x0, P0, params)
            obj.params = params;
            obj.x_hat = x0;
            obj.P = P0;
            
            % Process noise Q
            q_pos = (1e-3)^2;
            q_vel = (params.sensors.accel_noise_std)^2;
            q_att = (params.sensors.gyro_noise_std)^2;
            q_bias = (params.sensors.gyro_bias_std)^2;
            
            obj.Q = blkdiag(q_pos * eye(3), q_vel * eye(3), q_att * eye(3), q_bias * eye(3));
            
            % Measurement noise
            obj.R_star = (params.sensors.star_tracker_noise_std)^2 * eye(3);
            obj.R_range = (5.0)^2; % 5 meter 1-sigma DSN/GPS range noise
        end
        
        %% 1. Time Update (Prediction Step)
        function predict(obj, a_imu, omega_imu, dt, t_sec)
            r = obj.x_hat(1:3);
            v = obj.x_hat(4:6);
            q = obj.x_hat(7:10);
            bg = obj.x_hat(11:13);
            
            % Correct gyro measurement with estimated bias
            omega_corr = omega_imu - bg;
            
            % Transform measured specific force to inertial frame
            C_b2i = quaternion_utils.to_dcm(q);
            a_inertial = C_b2i * a_imu;
            
            % Add gravitational acceleration
            a_grav = gravity_field(r, t_sec, obj.params);
            a_total = a_inertial + a_grav;
            
            % Propagate position and velocity
            r_new = r + v * dt + 0.5 * a_total * dt^2;
            v_new = v + a_total * dt;
            
            % Propagate quaternion: q_new = q + 0.5 * Omega(omega_corr) * q * dt
            dq = quaternion_utils.derivative(q, omega_corr);
            q_new = quaternion_utils.normalize(q + dq * dt);
            
            % Bias random walk
            bg_new = bg;
            
            % Update estimated state
            obj.x_hat = [r_new; v_new; q_new; bg_new];
            
            % Discrete Error State Transition Matrix Phi (12x12)
            F = zeros(12, 12);
            F(1:3, 4:6) = eye(3);                      % dr/dv
            F(4:6, 7:9) = - C_b2i * skew(a_imu);       % dv/dtheta
            F(7:9, 7:9) = - skew(omega_corr);          % dtheta/dtheta
            F(7:9, 10:12) = - eye(3);                  % dtheta/dbg
            
            Phi = eye(12) + F * dt;
            
            % Propagate Covariance: P = Phi * P * Phi' + Q * dt
            obj.P = Phi * obj.P * Phi' + obj.Q * dt;
            obj.P = 0.5 * (obj.P + obj.P'); % Maintain symmetry
        end
        
        %% 2. Star Tracker Attitude Measurement Update
        function update_star_tracker(obj, q_meas)
            q_est = obj.x_hat(7:10);
            
            % Compute attitude error quaternion: delta_q = q_est^* (x) q_meas
            q_err = quaternion_utils.error(q_est, q_meas);
            
            % Small-angle approximation: delta_theta = 2 * delta_q(2:4)
            z_innov = 2.0 * q_err(2:4);
            
            % Measurement matrix H (3x12) for attitude error state
            H = zeros(3, 12);
            H(:, 7:9) = eye(3);
            
            % Kalman Gain
            S = H * obj.P * H' + obj.R_star;
            K = (obj.P * H') / S;
            
            % Error state correction
            delta_x = K * z_innov;
            
            % Apply corrections to state
            obj.x_hat(1:3) = obj.x_hat(1:3) + delta_x(1:3);
            obj.x_hat(4:6) = obj.x_hat(4:6) + delta_x(4:6);
            
            % Attitude quaternion multiplicative update
            dtheta = delta_x(7:9);
            dq_corr = [1.0; 0.5 * dtheta];
            obj.x_hat(7:10) = quaternion_utils.normalize(quaternion_utils.mult(q_est, dq_corr));
            
            % Gyro bias update
            obj.x_hat(11:13) = obj.x_hat(11:13) + delta_x(10:12);
            
            % Covariance update (Joseph form for numerical stability)
            I_KH = eye(12) - K * H;
            obj.P = I_KH * obj.P * I_KH' + K * obj.R_star * K';
            obj.P = 0.5 * (obj.P + obj.P');
        end
        
        %% 3. Range Measurement Update (DSN / Ground Tracking)
        function update_range(obj, range_meas)
            r = obj.x_hat(1:3);
            r_norm = norm(r);
            if r_norm < 1e-3
                return;
            end
            
            z_pred = r_norm;
            z_innov = range_meas - z_pred;
            
            H = zeros(1, 12);
            H(1:3) = (r / r_norm)';
            
            S = H * obj.P * H' + obj.R_range;
            K = (obj.P * H') / S;
            
            delta_x = K * z_innov;
            
            obj.x_hat(1:3) = obj.x_hat(1:3) + delta_x(1:3);
            obj.x_hat(4:6) = obj.x_hat(4:6) + delta_x(4:6);
            obj.x_hat(11:13) = obj.x_hat(11:13) + delta_x(10:12);
            
            I_KH = eye(12) - K * H;
            obj.P = I_KH * obj.P * I_KH' + K * obj.R_range * K';
            obj.P = 0.5 * (obj.P + obj.P');
        end
    end
end

%% Helper: Cross-Product Skew-Symmetric Matrix
function S = skew(v)
    S = [
            0, -v(3),  v(2);
         v(3),     0, -v(1);
        -v(2),  v(1),     0
    ];
end
