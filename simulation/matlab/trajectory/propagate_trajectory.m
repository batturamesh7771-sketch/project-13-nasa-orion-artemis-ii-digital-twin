%% Orion Trajectory Propagator (LEO, TLI, Lunar Flyby, Trans-Earth Return)
% Author: Senior Aerospace Engineer
% High-fidelity numerical integration (RK4) of translunar and return trajectory.

function traj = propagate_trajectory(params, sim_options)
    if nargin < 2
        sim_options.t_max_hours = 120; % 5 days of mission time
        sim_options.dt_sec = 60.0;     % 60 second step for orbital coast
    end
    
    mu_E = params.astro.mu_Earth;
    R_E = params.astro.R_Earth;
    
    %% 1. INITIAL ORBIT: LEO Parking Orbit (h = 185 km, inc = 28.5 deg KSC)
    h_leo = 185000.0; % 185 km altitude
    r_leo = R_E + h_leo;
    v_leo = sqrt(mu_E / r_leo); % ~7796 m/s circular velocity
    inc_rad = deg2rad(28.5);
    
    r0 = [r_leo; 0.0; 0.0];
    v0 = [0.0; v_leo * cos(inc_rad); v_leo * sin(inc_rad)];
    m0 = params.orbital.wet_mass_kg; % 25,618 kg
    
    %% 2. TRANSLUNAR INJECTION (TLI) BURN
    % Impulsive TLI burn executed by SLS Interim Cryogenic Propulsion Stage (ICPS)
    delta_v_tli = 3142.0; % m/s (Trans-Lunar Injection)
    v_tli_dir = v0 / norm(v0);
    v_post_tli = v0 + delta_v_tli * v_tli_dir;
    
    % Post-TLI: Orion stack separates from ICPS at full wet mass
    m_post_tli = params.orbital.wet_mass_kg; % 25,618 kg
    
    fprintf('[+] Translunar Injection (TLI) Burn (SLS ICPS Stage):\n');
    fprintf('    Pre-burn LEO Velocity : %.1f m/s\n', norm(v0));
    fprintf('    Delta-V Applied       : %.1f m/s\n', delta_v_tli);
    fprintf('    Post-burn Velocity    : %.1f m/s (C3 = %.2f km^2/s^2)\n', norm(v_post_tli), (norm(v_post_tli)^2 - 2*mu_E/r_leo)/1e6);
    fprintf('    Orion Mass Post-TLI   : %.1f kg (ESM Usable Propellant: %.1f kg)\n', m_post_tli, params.esm.propellant_usable_kg);

    %% 3. NUMERICAL INTEGRATION: RUNGE-KUTTA 4 (RK4)
    dt = sim_options.dt_sec;
    t_end = sim_options.t_max_hours * 3600.0;
    n_steps = floor(t_end / dt);
    
    t_arr = zeros(n_steps, 1);
    r_arr = zeros(n_steps, 3);
    v_arr = zeros(n_steps, 3);
    alt_arr = zeros(n_steps, 1);
    dist_moon_arr = zeros(n_steps, 1);
    mass_arr = zeros(n_steps, 1);
    stage_arr = strings(n_steps, 1);
    
    % Initial state
    t_cur = 0.0;
    r_cur = r0;
    v_cur = v_post_tli;
    m_cur = m_post_tli;
    
    min_dist_moon = 1e12;
    t_periapsis_moon = 0.0;
    reentry_detected = false;
    t_reentry = 0.0;
    
    for i = 1:n_steps
        t_arr(i) = t_cur;
        r_arr(i, :) = r_cur';
        v_arr(i, :) = v_cur';
        mass_arr(i) = m_cur;
        
        r_mag = norm(r_cur);
        alt_earth = r_mag - R_E;
        alt_arr(i) = alt_earth;
        
        % Lunar distance (matching transfer lead angle)
        theta_M = params.astro.theta_M0 + params.astro.omega_Moon * t_cur;
        r_Moon = [
            params.astro.dist_EM * cos(theta_M);
            params.astro.dist_EM * sin(theta_M) * cosd(5.14);
            params.astro.dist_EM * sin(theta_M) * sind(5.14)
        ];
        d_moon = norm(r_Moon - r_cur);
        dist_moon_arr(i) = d_moon;
        
        if d_moon < min_dist_moon
            min_dist_moon = d_moon;
            t_periapsis_moon = t_cur;
        end
        
        % Mission Phase Tagging
        if t_cur < 1800
            stage_arr(i) = "TLI_MANEUVER";
        elseif d_moon < 15000000 % Within 15,000 km of Moon
            stage_arr(i) = "LUNAR_FLYBY";
        elseif t_cur > t_periapsis_moon && min_dist_moon < 15000000
            stage_arr(i) = "TRANS_EARTH_RETURN";
        else
            stage_arr(i) = "TRANSLUNAR_COAST";
        end
        
        % Check for Atmospheric Entry Interface (EI-400 at h = 120 km) on return
        if t_cur > 86400 && alt_earth <= params.aero.entry_interface_alt_m && ~reentry_detected
            reentry_detected = true;
            t_reentry = t_cur;
            stage_arr(i) = "ENTRY_INTERFACE";
        end
        
        % RK4 Integration Steps
        k1_v = gravity_field(r_cur, t_cur, params);
        k1_r = v_cur;
        
        k2_v = gravity_field(r_cur + 0.5 * dt * k1_r, t_cur + 0.5 * dt, params);
        k2_r = v_cur + 0.5 * dt * k1_v;
        
        k3_v = gravity_field(r_cur + 0.5 * dt * k2_r, t_cur + 0.5 * dt, params);
        k3_r = v_cur + 0.5 * dt * k2_v;
        
        k4_v = gravity_field(r_cur + dt * k3_r, t_cur + dt, params);
        k4_r = v_cur + dt * k3_v;
        
        r_cur = r_cur + (dt / 6.0) * (k1_r + 2*k2_r + 2*k3_r + k4_r);
        v_cur = v_cur + (dt / 6.0) * (k1_v + 2*k2_v + 2*k3_v + k4_v);
        t_cur = t_cur + dt;
    end
    
    %% 4. PACKAGE TRAJECTORY RESULTS
    traj.time_sec = t_arr;
    traj.time_hours = t_arr / 3600.0;
    traj.pos_eci_m = r_arr;
    traj.vel_eci_m_s = v_arr;
    traj.altitude_earth_km = alt_arr / 1000.0;
    traj.dist_moon_km = dist_moon_arr / 1000.0;
    traj.mass_kg = mass_arr;
    traj.stage = stage_arr;
    traj.min_dist_moon_km = min_dist_moon / 1000.0;
    traj.lunar_altitude_km = (min_dist_moon - params.astro.R_Moon) / 1000.0;
    traj.t_periapsis_moon_hours = t_periapsis_moon / 3600.0;
    traj.reentry_detected = reentry_detected;
    traj.t_reentry_hours = t_reentry / 3600.0;
    
    fprintf('[+] Trajectory Propagation Complete:\n');
    fprintf('    Total Time Simulated : %.1f hours (%.2f days)\n', t_end/3600, t_end/86400);
    fprintf('    Closest Lunar Flyby : %.1f km altitude at MET %.1f hours\n', traj.lunar_altitude_km, traj.t_periapsis_moon_hours);
    fprintf('    Entry Interface (EI): %.1f hours MET\n', traj.t_reentry_hours);
end
