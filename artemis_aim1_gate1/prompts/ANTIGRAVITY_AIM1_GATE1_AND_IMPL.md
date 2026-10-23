# Antigravity task — Implement AIM 1 in the existing Artemis II Digital Twin

You are working inside the user's existing repository. The attached Gate 1 engineering pack is the source-of-truth starting point. The existing AIM 2 lunar trajectory and AIM 3 entry/recovery features are working and must be preserved.

## Mission rule that must not be violated

For real Artemis II chronology, AIM 1 cannot hand off to the lunar free-return trajectory at booster separation or core-stage MECO. NASA's timeline includes initial Earth-orbit and ICPS operations; Orion separates from ICPS, and Orion's service-module main engine performs TLI on Flight Day 2. NASA reports the completed TLI started at 7:49 p.m. EDT April 2, 2026, lasted 5 min 50 s, and delivered a reported 1,274 ft/s delta-v. AIM 2 begins from the generated *post-TLI Orion state*. See `data/aim1_source_registry.json` and `data/aim1_launch_event_reference.json`.

## Step 1 — inspect, do not assume

1. Inspect the full repository and current running app.
2. Locate the actual AIM 2 initialization API, state vector structure, unit conventions, frame realization, epoch/time scale, and trajectory outputs.
3. Locate AIM 3's entry-interface input contract.
4. Identify which tools are genuinely installed and callable: Python/SciPy, GMAT R2026a, SPICE/SpiceyPy if used, `simupy-flight` if used, and Three.js. Execute a harmless version/availability check; do not display a tool as integrated simply because its name exists in a label.
5. Preserve the present UI and all working AIM 2/AIM 3 behavior. Create an audit report before large edits.

## Step 2 — load and verify the supplied data files

Integrate, without copying values blindly:
- `data/aim1_source_registry.json`
- `data/aim1_launch_event_reference.json`
- `data/aim1_asset_manifest.json`
- `schemas/aim1_to_aim2_state.schema.json`

Run `python tools/validate_gate1_pack.py` in the pack if available. Copy/adapt the files into the actual project structure, and keep versions visible in simulation-run metadata. Verify each source directly before promoting a parameter into a dynamics model. Update or correct this pack's event record if a stronger official actual-mission source is found; keep an audit trail.

## Step 3 — implement AIM 1 in bounded modules

Fit the existing repository structure; likely create an `aim1` module with separate responsibilities:

- assembly/VAB/rollout/LC-39B deterministic visual sequence;
- vehicle config and versioned parameter/source registry;
- ascent numerical propagation;
- event detection/state-machine and stage-mass/configuration changes;
- early Earth-orbit, ICPS and Orion operations through TLI;
- post-TLI state adapter to existing AIM 2;
- independent numerical tests and validation report.

Do not insert physics equations into front-end rendering code. The front end receives timestamped calculated state. Three.js must render these outputs rather than a separately animated path.

### Visual sequence

Model the educational reconstruction in this order: major component/exploded view; booster/core-stage/ICPS/Orion integration; fully stacked vehicle inside VAB; mobile launcher and crawler rollout; LC-39B pad and umbilicals; terminal countdown; ignition/liftoff; ascent; visible separation events; orbit/ICPS operations; Orion TLI. Use NASA's SLS Block 1 and Orion public 3D assets where suitable, but inspect the actual downloaded assets for scale, axes, model contents and usage/attribution guidance. If VAB/pad assets are unavailable, create restrained procedural geometry and mark it as a visual reconstruction. Do not invent exact internal manufacturing procedures.

### Physics

Begin with a testable 3-DOF variable-mass model, unless the repository already contains a stronger validated launch model. Use a declared inertial frame; launch-site initial position/velocity must account for the rotating Earth; use a documented gravity model and atmosphere; compute atmospheric-relative speed, aerodynamic drag, dynamic pressure and Mach where the model is valid; integrate thrust and mass flow from sourced, versioned engine/booster histories; detect event functions numerically. At each staging event, change mass, active engines, configuration and force model consistently. Apply finite burns with documented thrust/ISP/mass histories.

**No fabricated thrust curves.** A published total liftoff thrust number is not a time-varying SRB/RS-25 thrust curve. Search for reliable open curves and vehicle inputs. If exact data is unavailable, explicitly label the reduced-order values as assumptions, include uncertainty/sensitivity analysis, and call the model an approximate/research simulation. Do not tune arbitrary curves solely to fake flight accuracy. Do not claim an SLS high-fidelity or 6-DOF model without the required inertia/aerodynamic/guidance/control data.

NASA `simupy-flight` and its NESC 6-DOF examples may be used to cross-check generic flight equations, but they are not an SLS model. GMAT is for orbit/maneuver cross-validation after the relevant orbital state is formed; it does not validate booster combustion or low-altitude launch aerodynamics. SPICE/Horizons planetary ephemerides are not Orion telemetry.

## Step 4 — use actual public checkpoints correctly

Keep the preflight Press Kit target timeline separate from the launch-day published event values. Implement a comparison report of calculated versus reference event times with source precision, model version and signed timing residual. The first ascent checkpoints include tower clear, supersonic, max-Q, SRB separation, LAS jettison, core MECO and core separation.

Continue through early orbit events and the Orion TLI burn. Record the NASA reported TLI duration and scalar delta-v as independent reference metrics. A reported scalar delta-v does not supply burn direction or full post-burn state. Calculate a self-consistent state through the equations and explicitly disclose calibration assumptions. Do not fabricate high-rate actual telemetry between sparse public events.

The post-TLI state must be the state generated by this run; if a public spacecraft trajectory or state-vector reference is available, compare against it with correct epoch, frame, and units.

## Step 5 — hand off to actual AIM 2 state

Use `schemas/aim1_to_aim2_state.schema.json` as a proposed canonical contract. First inspect AIM 2's actual schema. Keep a tested adapter between canonical SI values and the existing interface. Never silently change AIM 2 conventions or guess its state layout.

At the exact end of TLI, pass a consistent timestamped object that includes:
- epoch and MET;
- exact frame name and origin;
- position and velocity vectors;
- post-burn Orion/ESM mass and configuration;
- TLI duration and modeled delta-v vector if calculated;
- source/assumption manifest versions;
- fidelity tier, uncertainty summary and validation status.

Ensure no time gap, duplicate TLI burn, mass/configuration inconsistency or discontinuity in the state history. Add an integration test that starts AIM 2 from AIM 1's exact output state.

## Step 6 — validation gates

Implement tests for:
- units, frame conventions, source registry completeness and chronological event list;
- numerical integration convergence;
- zero-thrust/gravity-only and other analytical limiting cases;
- mass flow and component mass accounting;
- staging event resets and finite-burn handling;
- rotating-Earth launch-site velocity;
- event-time comparisons against the NASA public checkpoints;
- no invented event timestamps or silent fallback telemetry;
- round-trip state mapping and AIM 1 → AIM 2 continuity;
- GMAT matched-model orbital propagation after orbit insertion and/or after the TLI state, with position and velocity residuals at identical epochs;
- live API/Three.js showing the same calculated state and event timestamps.

Do not use GMAT residuals to certify low-altitude ascent physics. If source inputs are mismatched or any critical discrepancy remains unexplained, label that benchmark INCONCLUSIVE or FAIL.

## Step 7 — integrate the original UI

Add a clear AIM selector/timeline: AIM 1 Assembly & Launch; AIM 2 Earth–Moon Free-Return; AIM 3 Reentry & Recovery. The sequence should flow automatically when running the full mission but allow users to pause/seek/replay. Display separate visual-only assembly scenes and numerical flight scenes. Show simulation/reference provenance and active validation status in the UI. Preserve the existing polished dashboard and never render placeholder numbers as valid telemetry.

## Required deliverables

1. Repository audit and actual file map.
2. Changed files list.
3. Sourced parameter manifest and public reference timeline integrated into code.
4. Working assembly/VAB/rollout/pad/countedown scene sequence.
5. Launch/ascent numerical engine with declared fidelity and tests.
6. Orbit/ICPS/TLI continuation and a verified post-TLI adapter into existing AIM 2.
7. Real GMAT script/log/output/residuals for an orbital benchmark, or a truthful blocker report.
8. Test logs and timing/trajectory comparison reports.
9. Screenshot of the actual integrated browser experience.
10. Matrix of verified / calibrated / assumed / unimplemented features.

Do not finish by returning only a plan. Implement in small steps, run tests, launch the application, inspect the real browser output, and fix failures. Never say “fully verified” based only on unit-test counts, successful server startup, or UI labels.
