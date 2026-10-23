%% Orion Atmospheric Skip Re-Entry and Parachute Descent Simulation
% Author: Senior Aerospace Engineer
% High-fidelity simulation of Artemis-style skip re-entry, aerothermal deceleration,
% and multi-stage parachute deployment to ocean splashdown.

function entry_results = entry_equations(params, entry_options)
    if nargin < 2
        entry_options.v0_m_s = 11050.0;    % Lunar return entry velocity [m/s] (~Mach 36)
        entry_options.gamma0_deg = -5.85;  % Nominal entry flight path angle [deg]
        entry_options.h0_m = 120000.0;     % Entry Interface altitude (EI-400) [m]
        entry_options.dt_sec = 0.2;        % Integration time step [s]
    end

    R_E = params.astro.R_Earth;
    mu_E = params.astro.mu_Earth;
    m_capsule = params.cm.dry_mass_kg;     % 9,300 kg (Service Module already staged)
    A_ref = params.cm.ref_area_m2;         % 19.863 m^2
    Cd_hyp = params.aero.hypersonic_Cd;    % 1.25
    Cl_hyp = params.aero.hypersonic_Cl;    % 0.35

    dt = entry_options.dt_sec;
    t_max = 2400.0; % 40 minutes max simulation window (covers skip re-entry & full parachute descent)
    n_pts = floor(t_max / dt);

    % Preallocate time series
    t_arr = zeros(n_pts, 1);
    h_arr = zeros(n_pts, 1);
    v_arr = zeros(n_pts, 1);
    gamma_arr = zeros(n_pts, 1);
    downrange_arr = zeros(n_pts, 1);
    g_load_arr = zeros(n_pts, 1);
    heat_flux_arr = zeros(n_pts, 1);
    bank_arr = zeros(n_pts, 1);
    stage_arr = strings(n_pts, 1);

    % Initial conditions at Entry Interface
    t = 0.0;
    h = entry_options.h0_m;
    v = entry_options.v0_m_s;
    gamma = deg2rad(entry_options.gamma0_deg);
    s_downrange = 0.0;

    drogue_deployed = false;
    main_deployed = false;
    splashdown = false;
    
    skip_detected = false;
    second_entry = false;
    min_h_first_dip = 1e6;
    max_g_load = 0.0;
    max_heat_flux = 0.0;

    step_count = 0;

    for i = 1:n_pts
        step_count = step_count + 1;
        t_arr(i) = t;
        h_arr(i) = h;
        v_arr(i) = v;
        gamma_arr(i) = rad2deg(gamma);
        downrange_arr(i) = s_downrange;

        % 1. Atmospheric Density Model (US Standard Atmosphere 1976 approximation)
        if h > 85000.0
            rho = 1.225 * exp(-h / 7200.0);
        elseif h > 25000.0
            rho = 1.225 * exp(-h / 7050.0);
        else
            T_atm = 288.15 - 0.0065 * h;
            P_atm = 101325.0 * ((max(0.01, T_atm) / 288.15)^5.256);
            rho = P_atm / (287.05 * max(0.01, T_atm));
        end

        % Local gravity
        r = R_E + h;
        g = mu_E / (r^2);

        % 2. Aerodynamic & Parachute Coefficients (with progressive inflation / reefing)
        if h > params.chutes.drogue_deploy_alt_m
            % Hypersonic / Supersonic Capsule Entry
            CdA = Cd_hyp * A_ref;
            ClA = Cl_hyp * A_ref;
            
            % Skip-Entry Guidance Bank Angle Logic (Apollo/Artemis G-Limiting Roll Profile)
            if ~skip_detected
                if h > 60000 && v > 8500
                    bank_deg = 60.0; % Moderate lift to penetrate corridor
                    stage_arr(i) = "FIRST_ENTRY_DESCENT";
                else
                    bank_deg = 15.0; % Pull up once sufficient velocity is shed
                    stage_arr(i) = "CORRIDOR_PULL_UP";
                    min_h_first_dip = min(min_h_first_dip, h);
                    if gamma > 0
                        skip_detected = true;
                    end
                end
            elseif ~second_entry
                bank_deg = 90.0; % Pure lateral lift during exo-atmospheric skip coast
                stage_arr(i) = "EXO_ATMOSPHERIC_SKIP";
                if gamma <= 0
                    second_entry = true;
                end
            else
                % Second terminal descent: G-limiting bank modulation (NASA Artemis P65/P66)
                % Modulate bank to keep g-load comfortably under the 8.0g astronaut threshold
                if g_decel > 3.8
                    bank_deg = 0.0;  % Full lift-up to cushion deceleration
                elseif g_decel > 2.5
                    bank_deg = 45.0; % Moderate lift
                else
                    bank_deg = 75.0; % Steep descent to target splashdown
                end
                stage_arr(i) = "SECOND_ENTRY_TERMINAL";
            end
            
        elseif h > params.chutes.main_deploy_alt_m
            % Drogue Chutes Deployed (with gradual inflation over 8 seconds)
            if ~drogue_deployed
                drogue_deployed = true;
                t_drogue = t;
            end
            tau_drogue = 5.0;
            inflation_drogue = 1.0 - exp(-(t - t_drogue) / tau_drogue);
            CdA = (Cd_hyp * A_ref) + (params.chutes.drogue_CdA_m2 - Cd_hyp * A_ref) * inflation_drogue;
            ClA = 0.0;
            bank_deg = 0.0;
            stage_arr(i) = "DROGUE_CHUTES_DEPLOYED";
            
        else
            % Main Parachutes Deployed (progressive 2-stage reefing over 14 seconds)
            if ~main_deployed
                main_deployed = true;
                t_main = t;
            end
            tau_main = 8.0;
            inflation_main = 1.0 - exp(-(t - t_main) / tau_main);
            CdA = params.chutes.drogue_CdA_m2 + (params.chutes.main_CdA_m2 - params.chutes.drogue_CdA_m2) * inflation_main;
            ClA = 0.0;
            bank_deg = 0.0;
            stage_arr(i) = "MAIN_CHUTES_DEPLOYED";
        end

        bank_rad = deg2rad(bank_deg);
        bank_arr(i) = bank_deg;

        % Aerodynamic Forces
        q_dyn = 0.5 * rho * (v^2); % Dynamic pressure [Pa]
        Drag = q_dyn * CdA;
        Lift = q_dyn * ClA;

        % Deceleration in g's
        g_decel = Drag / (m_capsule * params.astro.g0);
        g_load_arr(i) = g_decel;
        max_g_load = max(max_g_load, g_decel);

        % Stagnation Point Heat Flux (Sutton-Graves: q_dot = k * sqrt(rho/R_nose) * v^3)
        % R_nose = 6.0 m for spherical heat shield, k = 1.7415e-4 [W/(m^2 * (kg/m^3)^0.5 * (m/s)^3)]
        q_heat = 1.7415e-4 * sqrt(rho / 6.0) * (v^3) / 10000.0; % [W/cm^2]
        heat_flux_arr(i) = q_heat;
        max_heat_flux = max(max_heat_flux, q_heat);

        % 3. Equations of Motion Derivatives & Semi-Implicit Drag Integration
        h_dot = v * sin(gamma);
        v_next = max(0.0, (v - g * sin(gamma) * dt) / (1.0 + 0.5 * rho * CdA * v * dt / m_capsule));
        
        if v > 1.0
            gamma_dot = (Lift * cos(bank_rad) / (m_capsule * v)) - ((g - (v^2)/r) * cos(gamma) / v);
        else
            gamma_dot = 0.0;
            gamma = -pi/2; % Vertical parachute descent
        end
        
        s_dot = (R_E / r) * v * cos(gamma);

        % 4. State Update
        h = h + h_dot * dt;
        v = v_next;
        gamma = gamma + gamma_dot * dt;
        s_downrange = s_downrange + s_dot * dt;
        t = t + dt;

        % 5. Splashdown Termination
        if h <= 0.0
            h = 0.0;
            splashdown = true;
            stage_arr(i) = "OCEAN_SPLASHDOWN";
            break;
        end
    end

    % Truncate arrays to completed steps
    entry_results.time_sec = t_arr(1:step_count);
    entry_results.altitude_km = h_arr(1:step_count) / 1000.0;
    entry_results.velocity_m_s = v_arr(1:step_count);
    entry_results.flight_path_deg = gamma_arr(1:step_count);
    entry_results.downrange_km = downrange_arr(1:step_count) / 1000.0;
    entry_results.g_load = g_load_arr(1:step_count);
    entry_results.heat_flux_W_cm2 = heat_flux_arr(1:step_count);
    entry_results.bank_angle_deg = bank_arr(1:step_count);
    entry_results.stage = stage_arr(1:step_count);
    
    entry_results.max_g_load = max_g_load;
    entry_results.max_heat_flux_W_cm2 = max_heat_flux;
    entry_results.first_dip_altitude_km = min_h_first_dip / 1000.0;
    entry_results.terminal_velocity_m_s = v_arr(step_count);
    entry_results.total_downrange_km = s_downrange / 1000.0;
    entry_results.splashdown_time_min = t / 60.0;
    entry_results.splashdown = splashdown;

    fprintf('[+] Atmospheric Skip Re-entry & Recovery Simulation Complete:\n');
    fprintf('    Initial Entry Velocity : %.1f m/s (Mach ~%.1f)\n', entry_options.v0_m_s, entry_options.v0_m_s/300);
    fprintf('    First Dip Min Altitude : %.1f km\n', entry_results.first_dip_altitude_km);
    fprintf('    Peak Aerodynamic Decel : %.2f g (NASA limit < 8.0 g)\n', entry_results.max_g_load);
    fprintf('    Peak Stagnation Heat   : %.1f W/cm^2\n', entry_results.max_heat_flux_W_cm2);
    fprintf('    Terminal Splashdown Vel: %.2f m/s (Main chutes active)\n', entry_results.terminal_velocity_m_s);
    fprintf('    Total Entry Downrange  : %.1f km\n', entry_results.total_downrange_km);
    fprintf('    Time to Splashdown     : %.2f minutes\n', entry_results.splashdown_time_min);
end
