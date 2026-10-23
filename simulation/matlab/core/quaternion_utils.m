%% Quaternion Utilities Library for Spacecraft GNC
% Author: Senior Aerospace Engineer
% NASA Convention: q = [q0; q1; q2; q3], where q0 is the scalar part, [q1; q2; q3] is the vector part.

classdef quaternion_utils
    methods (Static)
        %% 1. Quaternion Multiplication (Hamilton Product)
        function q = mult(q1, q2)
            s1 = q1(1); v1 = q1(2:4);
            s2 = q2(1); v2 = q2(2:4);
            
            s = s1 * s2 - dot(v1, v2);
            v = s1 * v2 + s2 * v1 + cross(v1, v2);
            q = [s; v];
        end

        %% 2. Quaternion Conjugate
        function q_c = conj(q)
            q_c = [q(1); -q(2:4)];
        end

        %% 3. Quaternion Normalization
        function q_n = normalize(q)
            n = norm(q);
            if n < 1e-12
                q_n = [1; 0; 0; 0];
            else
                q_n = q / n;
            end
        end

        %% 4. Rotate Vector by Quaternion: v_rot = q * [0; v] * q^*
        function v_rot = rot(q, v)
            q_v = [0; v(:)];
            q_res = quaternion_utils.mult(quaternion_utils.mult(q, q_v), quaternion_utils.conj(q));
            v_rot = q_res(2:4);
        end

        %% 5. Quaternion Error: q_err = q_target^* (x) q_current
        function q_err = error(q_target, q_current)
            q_err = quaternion_utils.mult(quaternion_utils.conj(q_target), q_current);
            % Ensure scalar part is positive for shortest rotation path
            if q_err(1) < 0
                q_err = -q_err;
            end
        end

        %% 6. Convert Quaternion to Direction Cosine Matrix (Body-to-Inertial)
        function C = to_dcm(q)
            q0 = q(1); q1 = q(2); q2 = q(3); q3 = q(4);
            C = [
                1 - 2*(q2^2 + q3^2),     2*(q1*q2 - q0*q3),     2*(q1*q3 + q0*q2);
                    2*(q1*q2 + q0*q3), 1 - 2*(q1^2 + q3^2),     2*(q2*q3 - q0*q1);
                    2*(q1*q3 - q0*q2),     2*(q2*q3 + q0*q1), 1 - 2*(q1^2 + q2^2)
            ];
        end

        %% 7. Convert DCM to Quaternion (Shepperd's Algorithm)
        function q = from_dcm(C)
            tr = trace(C);
            if tr > 0
                s = 0.5 / sqrt(tr + 1.0);
                q0 = 0.25 / s;
                q1 = (C(3,2) - C(2,3)) * s;
                q2 = (C(1,3) - C(3,1)) * s;
                q3 = (C(2,1) - C(1,2)) * s;
            elseif (C(1,1) > C(2,2)) && (C(1,1) > C(3,3))
                s = 2.0 * sqrt(1.0 + C(1,1) - C(2,2) - C(3,3));
                q0 = (C(3,2) - C(2,3)) / s;
                q1 = 0.25 * s;
                q2 = (C(1,2) + C(2,1)) / s;
                q3 = (C(1,3) + C(3,1)) / s;
            elseif C(2,2) > C(3,3)
                s = 2.0 * sqrt(1.0 + C(2,2) - C(1,1) - C(3,3));
                q0 = (C(1,3) - C(3,1)) / s;
                q1 = (C(1,2) + C(2,1)) / s;
                q2 = 0.25 * s;
                q3 = (C(2,3) + C(3,2)) / s;
            else
                s = 2.0 * sqrt(1.0 + C(3,3) - C(1,1) - C(2,2));
                q0 = (C(2,1) - C(1,2)) / s;
                q1 = (C(1,3) + C(3,1)) / s;
                q2 = (C(2,3) + C(3,2)) / s;
                q3 = 0.25 * s;
            end
            q = quaternion_utils.normalize([q0; q1; q2; q3]);
        end

        %% 8. Euler Angles (Roll-Pitch-Yaw, 3-2-1) to Quaternion
        function q = from_euler(roll, pitch, yaw)
            cr = cos(roll / 2);  sr = sin(roll / 2);
            cp = cos(pitch / 2); sp = sin(pitch / 2);
            cy = cos(yaw / 2);   sy = sin(yaw / 2);

            q0 = cy * cp * cr + sy * sp * sr;
            q1 = cy * cp * sr - sy * sp * cr;
            q2 = cy * sp * cr + sy * cp * sr;
            q3 = sy * cp * cr - cy * sp * sr;
            q = quaternion_utils.normalize([q0; q1; q2; q3]);
        end

        %% 9. Quaternion to Euler Angles (Roll, Pitch, Yaw in radians)
        function [roll, pitch, yaw] = to_euler(q)
            q0 = q(1); q1 = q(2); q2 = q(3); q3 = q(4);
            
            % Roll (x-axis rotation)
            sinr_cosp = 2 * (q0 * q1 + q2 * q3);
            cosr_cosp = 1 - 2 * (q1^2 + q2^2);
            roll = atan2(sinr_cosp, cosr_cosp);

            % Pitch (y-axis rotation)
            sinp = 2 * (q0 * q2 - q3 * q1);
            if abs(sinp) >= 1
                pitch = sign(sinp) * (pi / 2); % Gimbal lock
            else
                pitch = asin(sinp);
            end

            % Yaw (z-axis rotation)
            siny_cosp = 2 * (q0 * q3 + q1 * q2);
            cosy_cosp = 1 - 2 * (q2^2 + q3^2);
            yaw = atan2(siny_cosp, cosy_cosp);
        end
        
        %% 10. Quaternion Kinematic Derivative: dq/dt = 0.5 * Omega(omega) * q
        function dq = derivative(q, omega)
            wx = omega(1); wy = omega(2); wz = omega(3);
            Omega = [
                  0, -wx, -wy, -wz;
                 wx,   0,  wz, -wy;
                 wy, -wz,   0,  wx;
                 wz,  wy, -wx,   0
            ];
            dq = 0.5 * Omega * q(:);
        end
    end
end
