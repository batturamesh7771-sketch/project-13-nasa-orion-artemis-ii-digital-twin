%% Unit Test: Trajectory Propagation and Skip Re-Entry Verification
% Author: Senior Aerospace Engineer
% Verifies orbital propagation, lunar flyby, and atmospheric recovery limits.

function passed = test_trajectory_and_entry()
    fprintf('[*] Running Test: Trajectory and Atmospheric Recovery...\n');
    passed = true;
    
    params = orion_params();
    
    %% 1. Trajectory Propagation Test
    options.t_max_hours = 96.0; % 4 days
    options.dt_sec = 120.0;     % 2 min step
    traj = propagate_trajectory(params, options);
    
    assert(traj.lunar_altitude_km > 0.0, 'Spacecraft impacted lunar surface');
    assert(traj.lunar_altitude_km < 10000.0, 'Failed to achieve lunar flyby within 10,000 km');
    fprintf('    Lunar Closest Approach  : %.1f km altitude (Verified flyby)\n', traj.lunar_altitude_km);
    
    %% 2. Atmospheric Skip Re-entry and Parachute Test
    entry_opt.v0_m_s = 11050.0;
    entry_opt.gamma0_deg = -5.85;
    entry_opt.h0_m = 120000.0;
    entry_opt.dt_sec = 0.2;
    
    entry_res = entry_equations(params, entry_opt);
    
    assert(entry_res.splashdown == true, 'Spacecraft failed to reach ocean splashdown');
    assert(entry_res.max_g_load < 8.0, 'Peak g-load exceeded NASA astronaut limit of 8.0 g');
    assert(entry_res.max_heat_flux_W_cm2 < 250.0, 'Heat flux exceeded Avcoat TPS threshold');
    assert(entry_res.terminal_velocity_m_s < 10.0, 'Terminal splashdown velocity too high (>10 m/s)');
    assert(entry_res.first_dip_altitude_km > 50.0, 'First dip went dangerously low (<50 km)');
    
    fprintf('    First Dip Altitude      : %.1f km\n', entry_res.first_dip_altitude_km);
    fprintf('    Peak G-Load             : %.2f g (Limit: 8.0 g)\n', entry_res.max_g_load);
    fprintf('    Peak Stagnation Heating : %.1f W/cm^2\n', entry_res.max_heat_flux_W_cm2);
    fprintf('    Terminal Splashdown Vel : %.2f m/s (Limit: 10.0 m/s)\n', entry_res.terminal_velocity_m_s);
    
    fprintf('    [PASS] Trajectory and Skip Re-entry limits verified.\n');
end
