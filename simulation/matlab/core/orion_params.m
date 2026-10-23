%% Orion Digital Twin - Phase 3 Core Parameters
% Author: Senior Aerospace Engineer
% Defines complete physical, orbital, propulsion, mass properties, and aerodynamic specifications.

function params = orion_params()
    %% 1. ASTRODYNAMICAL CONSTANTS
    params.astro.G = 6.67430e-11;             % Gravitational constant [m^3/(kg*s^2)]
    params.astro.mu_Earth = 3.986004418e14;   % Earth gravitational parameter [m^3/s^2]
    params.astro.R_Earth = 6378137.0;         % Earth equatorial radius [m]
    params.astro.J2_Earth = 1.08263e-3;       % Earth J2 oblateness harmonic
    params.astro.omega_Earth = 7.2921159e-5;  % Earth rotation rate [rad/s]
    
    params.astro.mu_Moon = 4.9048695e12;      % Moon gravitational parameter [m^3/s^2]
    params.astro.R_Moon = 1737400.0;          % Moon mean radius [m]
    params.astro.dist_EM = 384400000.0;       % Earth-Moon mean orbital distance [m]
    params.astro.omega_Moon = 2.6617e-6;      % Moon orbital angular velocity [rad/s]
    params.astro.theta_M0 = deg2rad(126.0);   % Nominal initial Moon phase angle at TLI [rad]
    
    params.astro.g0 = 9.80665;                % Standard gravitational acceleration [m/s^2]

    %% 2. SPACECRAFT MASS & INERTIA PROPERTIES
    % Crew Module (CM)
    params.cm.base_diameter_m = 5.029;
    params.cm.height_m = 3.350;
    params.cm.ref_area_m2 = pi * (5.029/2)^2;  % 19.863 m^2
    params.cm.dry_mass_kg = 9300.0;
    params.cm.cg_offset_m = [0.05; 0.0; 0.0];  % +5 cm radial CG offset for trim AoA
    params.cm.inertia = [
        7200,    0,    0;
           0, 7500,    0;
           0,    0, 6800
    ]; % [kg*m^2]
    
    % European Service Module (ESM)
    params.esm.diameter_m = 5.000;
    params.esm.height_m = 4.000;
    params.esm.dry_mass_kg = 7700.0;
    params.esm.propellant_usable_kg = 8618.0;
    params.esm.wet_mass_kg = params.esm.dry_mass_kg + params.esm.propellant_usable_kg; % 16318 kg
    
    % Orbital Flight Configuration (CM + ESM Wet)
    params.orbital.wet_mass_kg = params.cm.dry_mass_kg + params.esm.wet_mass_kg; % 25618 kg
    params.orbital.inertia = [
        45000,     0,     0;
            0, 48000,     0;
            0,     0, 18000
    ]; % [kg*m^2]
    
    % Full Launch Stack (with LAS)
    params.stack.total_mass_kg = 35380.0;

    %% 3. PROPULSION SYSTEMS
    % Central OMS-E Main Engine (AJ10-190 derivative)
    params.omse.thrust_N = 26700.0;           % 6,000 lbf
    params.omse.Isp_s = 316.0;               % Specific impulse [s]
    params.omse.mdot_kg_s = params.omse.thrust_N / (params.omse.Isp_s * params.astro.g0);
    params.omse.gimbal_limit_deg = 7.0;       % TVC limit [deg]
    
    % 8 ESM Auxiliary Thrusters (Aerojet R-4D-11)
    params.aux.thrust_N = 490.0;              % 490 N per engine
    params.aux.Isp_s = 312.0;                % Specific impulse [s]
    params.aux.count = 8;
    params.aux.radius_m = 1.85;               % Mounted at 1.85 m radius
    
    % 12 CM Reaction Control System (RCS) Thrusters
    params.rcs.thrust_N = 160.0;              % 160 N per pulse thruster
    params.rcs.Isp_s = 290.0;                % Specific impulse [s]
    params.rcs.count = 12;

    %% 4. ATTITUDE CONTROL & GNC
    params.gnc.sample_time_s = 0.05;          % 20 Hz GNC loop
    params.gnc.kp_attitude = 3500.0;          % Proportional gain [Nm/rad]
    params.gnc.kd_attitude = 12000.0;         % Derivative gain [Nm/(rad/s)]
    params.gnc.max_torque_Nm = 3500.0;        % Max control torque [Nm]
    params.gnc.deadband_deg = 0.1;            % Attitude deadband [deg]
    params.gnc.rate_limit_deg_s = 2.0;        % Slew rate limit [deg/s]

    %% 5. SENSOR SPECIFICATIONS & NOISE (EKF TUNING)
    % IMU Gyroscope
    params.sensors.gyro_noise_std = 1.5e-4;    % Angle Random Walk [rad/s/sqrt(Hz)]
    params.sensors.gyro_bias_std = 2.0e-5;     % In-run bias instability [rad/s]
    % IMU Accelerometer
    params.sensors.accel_noise_std = 2.0e-3;   % Velocity Random Walk [m/s^2/sqrt(Hz)]
    params.sensors.accel_bias_std = 5.0e-4;    % Bias instability [m/s^2]
    % Star Tracker
    params.sensors.star_tracker_noise_std = 5.0e-5; % Pointing noise [rad] (10 arcsec)
    params.sensors.star_tracker_rate_hz = 5.0;      % 5 Hz update rate

    %% 6. AERODYNAMICS & RE-ENTRY CORRIDOR
    params.aero.ref_area_m2 = params.cm.ref_area_m2;
    params.aero.ref_length_m = params.cm.base_diameter_m;
    params.aero.trim_aoa_deg = -18.0;         % Trim angle of attack [deg]
    params.aero.hypersonic_Cd = 1.25;         % Hypersonic drag coefficient
    params.aero.hypersonic_Cl = 0.35;         % Hypersonic lift coefficient
    params.aero.hypersonic_LD = 0.28;         % Trim L/D ratio
    params.aero.entry_interface_alt_m = 120000.0; % Entry Interface (EI-400) [m]
    params.aero.skip_apogee_alt_m = 85000.0;  % Skip apogee target altitude [m]
    
    %% 7. PARACHUTE RECOVERY SEQUENCE
    params.chutes.fbc_jettison_alt_m = 7900.0; % Forward Bay Cover jettison [m]
    params.chutes.drogue_deploy_alt_m = 7600.0;% 2 Drogue chutes (7.0 m dia)
    params.chutes.drogue_CdA_m2 = 2 * 0.55 * (pi * 3.5^2); % ~42 m^2
    params.chutes.main_deploy_alt_m = 2900.0;  % 3 Main chutes (35.4 m dia)
    params.chutes.main_CdA_m2 = 3 * 0.75 * (pi * 17.7^2);  % ~2200 m^2
    params.chutes.splashdown_vel_m_s = 7.5;    % Terminal velocity at splashdown [m/s]
end
