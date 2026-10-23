%% Master Simulation Runner — Phase 3: MATLAB Engineering Simulation
% Author: Senior Aerospace Engineer
% NASA Orion Digital Twin: 6-DOF GNC, Trajectory Propagation & EKF Navigation

function all_passed = run_phase3_simulation()
    fprintf('=================================================================\n');
    fprintf('   NASA ORION DIGITAL TWIN — PHASE 3 SIMULATION TEST HARNESS     \n');
    fprintf('=================================================================\n\n');
    
    % Initialize paths
    currentFile = mfilename('fullpath');
    [testDir, ~, ~] = fileparts(currentFile);
    projectRoot = fullfile(testDir, '..', '..');
    
    addpath(genpath(fullfile(projectRoot, 'simulation', 'matlab')));
    
    test_results = struct();
    all_passed = true;
    
    %% Test 1: Quaternion Utilities
    try
        test_results.quaternion = test_quaternion_utils();
    catch ME
        fprintf('    [FAIL] Quaternion Utilities failed: %s\n', ME.message);
        test_results.quaternion = false;
        all_passed = false;
    end
    fprintf('\n');

    %% Test 2: Attitude Control Dynamics
    try
        test_results.attitude = test_attitude_control();
    catch ME
        fprintf('    [FAIL] Attitude Control failed: %s\n', ME.message);
        test_results.attitude = false;
        all_passed = false;
    end
    fprintf('\n');

    %% Test 3: Extended Kalman Filter Navigation
    try
        test_results.ekf = test_ekf();
    catch ME
        fprintf('    [FAIL] EKF Navigation failed: %s\n', ME.message);
        test_results.ekf = false;
        all_passed = false;
    end
    fprintf('\n');

    %% Test 4: Trajectory Propagation & Skip Re-entry
    try
        test_results.trajectory_and_entry = test_trajectory_and_entry();
    catch ME
        fprintf('    [FAIL] Trajectory & Entry failed: %s\n', ME.message);
        test_results.trajectory_and_entry = false;
        all_passed = false;
    end
    fprintf('\n');

    %% Export Sample Telemetry JSON for Phase 5 Dashboard Integration
    try
        fprintf('[*] Generating and Exporting High-Rate Simulated Telemetry...\n');
        params = orion_params();
        entry_opt.v0_m_s = 11050.0;
        entry_opt.gamma0_deg = -5.85;
        entry_opt.h0_m = 120000.0;
        entry_opt.dt_sec = 0.2; % 0.2s step for numerical integration stability
        
        entry_data = entry_equations(params, entry_opt);
        
        % Package JSON Telemetry
        telemetry.provenance = "[SIMULATED]";
        telemetry.spacecraft = "NASA Orion MPCV";
        telemetry.mission = "Artemis Lunar Return & Skip Re-entry";
        telemetry.timestamp_utc = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z'''));
        telemetry.simulation_time_sec = entry_data.time_sec(1:min(300, length(entry_data.time_sec)));
        telemetry.altitude_km = entry_data.altitude_km(1:min(300, length(entry_data.altitude_km)));
        telemetry.velocity_m_s = entry_data.velocity_m_s(1:min(300, length(entry_data.velocity_m_s)));
        telemetry.g_load = entry_data.g_load(1:min(300, length(entry_data.g_load)));
        telemetry.heat_flux_W_cm2 = entry_data.heat_flux_W_cm2(1:min(300, length(entry_data.heat_flux_W_cm2)));
        telemetry.bank_angle_deg = entry_data.bank_angle_deg(1:min(300, length(entry_data.bank_angle_deg)));
        telemetry.stage = entry_data.stage(1:min(300, length(entry_data.stage)));
        
        telemetry_dir = fullfile(projectRoot, 'telemetry');
        if ~exist(telemetry_dir, 'dir')
            mkdir(telemetry_dir);
        end
        
        json_file = fullfile(telemetry_dir, 'mission_telemetry_simulated.json');
        json_str = jsonencode(telemetry, 'PrettyPrint', true);
        fid = fopen(json_file, 'w');
        fwrite(fid, json_str, 'char');
        fclose(fid);
        
        fprintf('[+] Saved Mission Telemetry to: %s\n\n', json_file);
    catch ME
        fprintf('[!] Warning: Failed to export telemetry JSON: %s\n\n', ME.message);
    end

    %% Summary Table
    fprintf('=================================================================\n');
    fprintf('               PHASE 3 VERIFICATION SUMMARY                      \n');
    fprintf('=================================================================\n');
    fprintf('  Module 1: Quaternion Arithmetic & Kinematics : %s\n', get_status(test_results.quaternion));
    fprintf('  Module 2: 6-DOF Attitude Dynamics & Control  : %s\n', get_status(test_results.attitude));
    fprintf('  Module 3: Multiplicative EKF State Estimator : %s\n', get_status(test_results.ekf));
    fprintf('  Module 4: Lunar Trajectory & Skip Re-Entry   : %s\n', get_status(test_results.trajectory_and_entry));
    fprintf('=================================================================\n');
    if all_passed
        fprintf('  STATUS: ALL PHASE 3 SIMULATION MODULES VERIFIED (PASSED)\n');
    else
        fprintf('  STATUS: SOME MODULES FAILED\n');
    end
    fprintf('=================================================================\n');
end

function str = get_status(val)
    if val
        str = 'PASSED [OK]';
    else
        str = 'FAILED [ERROR]';
    end
end
