%% Unit Test: Quaternion Utilities Verification
% Author: Senior Aerospace Engineer

function passed = test_quaternion_utils()
    fprintf('[*] Running Test: Quaternion Utilities...\n');
    passed = true;
    
    % Test 1: Normalization
    q_unnorm = [3.0; 4.0; 0.0; 0.0];
    q_norm = quaternion_utils.normalize(q_unnorm);
    assert(abs(norm(q_norm) - 1.0) < 1e-12, 'Normalization failed');
    
    % Test 2: Multiplication Identity
    q_id = [1.0; 0.0; 0.0; 0.0];
    q_test = quaternion_utils.normalize([0.5; -0.3; 0.8; 0.1]);
    q_prod = quaternion_utils.mult(q_test, q_id);
    assert(norm(q_prod - q_test) < 1e-12, 'Identity multiplication failed');
    
    % Test 3: Conjugate and Inverse Product: q (x) q^* = [1; 0; 0; 0]
    q_inv_prod = quaternion_utils.mult(q_test, quaternion_utils.conj(q_test));
    assert(norm(q_inv_prod - q_id) < 1e-12, 'Inverse product failed');
    
    % Test 4: Vector Rotation (90 deg about Z axis)
    q_z90 = quaternion_utils.from_euler(0, 0, pi/2);
    v_x = [1.0; 0.0; 0.0];
    v_rot = quaternion_utils.rot(q_z90, v_x);
    expected_v = [0.0; 1.0; 0.0];
    assert(norm(v_rot - expected_v) < 1e-10, '90 deg Z rotation failed');
    
    % Test 5: DCM Round-Trip
    C = quaternion_utils.to_dcm(q_test);
    q_recovered = quaternion_utils.from_dcm(C);
    % Check parity (q and -q represent same rotation)
    assert(min(norm(q_recovered - q_test), norm(q_recovered + q_test)) < 1e-10, 'DCM round-trip failed');
    
    fprintf('    [PASS] All Quaternion Utilities unit tests passed.\n');
end
