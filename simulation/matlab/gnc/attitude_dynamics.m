%% Orion 6-DOF Nonlinear Attitude Dynamics
% Author: Senior Aerospace Engineer
% Propagates quaternion kinematics and Euler rotational equations of motion.

function xdot = attitude_dynamics(t, x, tau_ext, J)
    % State vector:
    % x(1:4) = q (quaternion [q0; q1; q2; q3])
    % x(5:7) = omega (angular velocity [wx; wy; wz] in body frame [rad/s])
    
    q = x(1:4);
    omega = x(5:7);
    
    % Enforce unit quaternion normalization
    q = quaternion_utils.normalize(q);
    
    % 1. Quaternion Kinematic Derivative: dq/dt = 0.5 * Omega(omega) * q
    dq = quaternion_utils.derivative(q, omega);
    
    % 2. Euler Rotational Dynamics: J * domega/dt = tau_ext - omega x (J * omega)
    H = J * omega; % Angular momentum vector
    gyroscopic_torque = cross(omega, H);
    
    domega = J \ (tau_ext - gyroscopic_torque);
    
    % Pack derivative
    xdot = [dq; domega];
end
