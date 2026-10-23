%% Gravitational Acceleration with J2 Oblateness and Moon 3rd-Body Perturbation
% Author: Senior Aerospace Engineer
% Computes total gravitational acceleration in Earth-Centered Inertial (ECI) frame.

function a_grav = gravity_field(r_vec, t_sec, params)
    r = norm(r_vec);
    if r < 1e-3
        a_grav = [0; 0; 0];
        return;
    end
    
    mu_E = params.astro.mu_Earth;
    R_E = params.astro.R_Earth;
    J2 = params.astro.J2_Earth;
    mu_M = params.astro.mu_Moon;
    d_EM = params.astro.dist_EM;
    omega_M = params.astro.omega_Moon;

    %% 1. Earth Central Point-Mass Gravity
    a_central = - (mu_E / (r^3)) * r_vec;

    %% 2. Earth J2 Zonal Oblateness Perturbation
    x = r_vec(1); y = r_vec(2); z = r_vec(3);
    z2_r2 = (z / r)^2;
    factor = -1.5 * J2 * mu_E * (R_E^2) / (r^5);
    
    a_J2 = [
        factor * x * (1 - 5 * z2_r2);
        factor * y * (1 - 5 * z2_r2);
        factor * z * (3 - 5 * z2_r2)
    ];

    %% 3. Moon Third-Body Gravitation (Ephemeris-Driven with Transfer Lead Angle)
    if isfield(params.astro, 'theta_M0')
        theta_M0 = params.astro.theta_M0;
    else
        theta_M0 = deg2rad(126.0);
    end
    theta_M = theta_M0 + omega_M * t_sec;
    r_Moon = [
        d_EM * cos(theta_M);
        d_EM * sin(theta_M) * cosd(5.14); % 5.14 deg Moon orbital inclination
        d_EM * sin(theta_M) * sind(5.14)
    ];
    
    % Vector from Spacecraft to Moon
    r_sc_to_moon = r_Moon - r_vec;
    d_sc_moon = norm(r_sc_to_moon);
    d_moon = norm(r_Moon);
    
    a_third_body = mu_M * ( (r_sc_to_moon / (d_sc_moon^3)) - (r_Moon / (d_moon^3)) );

    %% Total Gravitational Acceleration
    a_grav = a_central + a_J2 + a_third_body;
end
