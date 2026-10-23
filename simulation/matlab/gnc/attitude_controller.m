%% Orion Closed-Loop Quaternion Feedback Attitude Controller
% Author: Senior Aerospace Engineer
% Implements Lyapunov-stable quaternion error feedback PD control with torque saturation.

function [tau_cmd, q_err] = attitude_controller(q_target, q_current, omega_current, omega_target, params)
    if nargin < 4 || isempty(omega_target)
        omega_target = [0; 0; 0];
    end
    
    Kp = params.gnc.kp_attitude;       % Proportional gain [Nm/rad]
    Kd = params.gnc.kd_attitude;       % Derivative gain [Nm/(rad/s)]
    tau_max = params.gnc.max_torque_Nm;% Max control torque [Nm]
    
    % 1. Compute Error Quaternion: q_err = q_target^* (x) q_current
    q_err = quaternion_utils.error(q_target, q_current);
    
    % Extract vector part of error quaternion
    % The vector part q_err(2:4) represents sin(theta/2) * e_axis
    q_v = q_err(2:4);
    
    % 2. Rate Error
    omega_err = omega_current - omega_target;
    
    % 3. Control Torque Law: tau = -Kp * q_v - Kd * omega_err
    tau_raw = - Kp * q_v - Kd * omega_err;
    
    % 4. Actuator Saturation Limit
    tau_mag = norm(tau_raw);
    if tau_mag > tau_max
        tau_cmd = (tau_raw / tau_mag) * tau_max;
    else
        tau_cmd = tau_raw;
    end
end
