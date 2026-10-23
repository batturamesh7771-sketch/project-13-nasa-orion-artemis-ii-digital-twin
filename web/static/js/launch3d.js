/**
 * NASA SLS Block 1 & Orion Launch 3D Visualizer (AIM 1).
 * Features:
 *   - Procedural Kennedy Space Center Pad LC-39B & Mobile Launcher 1 tower
 *   - High-fidelity SLS Block 1 3D vehicle model (Core, 4x RS-25, 2x SRBs, ICPS, Orion, LAS)
 *   - Dynamic rocket exhaust plumes & staging separations (SRB sep, LAS jettison, MECO)
 *   - 5 Educational Reconstruction Scenes:
 *       1. PARTS: Exploded hardware elements
 *       2. VAB STACK: High Bay 3 integration sequence
 *       3. ROLLOUT: Crawler-Transporter 2 rollout to LC-39B
 *       4. PAD READY: Terminal countdown & umbilical release
 *       5. FLIGHT: Active 3-DOF numerical ascent flight
 */

class SLSLaunchViewer3D {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.warn('SLSLaunchViewer3D: canvas not found:', canvasId);
      return;
    }

    this.sceneMode = 'flight'; // 'parts', 'vab_stack', 'rollout', 'pad_ready', 'flight'
    this.altitude_km = 0.0;
    this.velocity_m_s = 0.0;
    this.mach = 0.0;
    this.stage = 'SLS_FIRST_STAGE_BOOSTERS';
    this.met_s = 0.0;

    this.initThree();
    this.setupLighting();
    this.buildScene();
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  initThree() {
    const width = this.canvas.parentElement ? this.canvas.parentElement.clientWidth : 800;
    const height = this.canvas.parentElement ? this.canvas.parentElement.clientHeight : 500;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x040a18);
    this.scene.fog = new THREE.FogExp2(0x040a18, 0.0008);

    this.camera = new THREE.PerspectiveCamera(45, width / Math.max(height, 1), 0.5, 5000);
    this.camera.position.set(135, 72, 155);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;

    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxPolarAngle = Math.PI / 2 + 0.05;
      this.controls.minDistance = 20;
      this.controls.maxDistance = 1200;
      this.controls.target.set(0, 56, 0);
    }

    window.addEventListener('resize', () => this.onResize());
  }

  onResize() {
    if (!this.canvas || !this.canvas.parentElement) return;
    const w = this.canvas.parentElement.clientWidth;
    const h = this.canvas.parentElement.clientHeight;
    if (w === 0 || h === 0) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  setupLighting() {
    // Sunlight
    this.sunLight = new THREE.DirectionalLight(0xfff6e6, 1.4);
    this.sunLight.position.set(200, 300, 150);
    this.sunLight.castShadow = true;
    this.scene.add(this.sunLight);

    // Deep space fill light
    const ambientLight = new THREE.AmbientLight(0x3a5477, 0.65);
    this.scene.add(ambientLight);

    // Launch plume light (dynamic)
    this.plumeLight = new THREE.PointLight(0xff7700, 0, 150);
    this.plumeLight.position.set(0, -5, 0);
    this.scene.add(this.plumeLight);
  }

  buildScene() {
    // 1. Terrain & Pad Foundation
    this.padGroup = new THREE.Group();
    this.scene.add(this.padGroup);

    // Ground plane
    const groundGeo = new THREE.PlaneGeometry(1200, 1200, 32, 32);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x1a2634,
      roughness: 0.9,
      metalness: 0.1
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -2;
    ground.receiveShadow = true;
    this.padGroup.add(ground);

    // Pad Concrete Hardstand (octagonal pyramid)
    const padBaseGeo = new THREE.CylinderGeometry(60, 75, 6, 8);
    const padBaseMat = new THREE.MeshStandardMaterial({ color: 0x485868, roughness: 0.85 });
    const padBase = new THREE.Mesh(padBaseGeo, padBaseMat);
    padBase.position.y = 1;
    padBase.receiveShadow = true;
    this.padGroup.add(padBase);

    // Mobile Launcher 1 Base Platform
    const mlBaseGeo = new THREE.BoxGeometry(45, 10, 40);
    const mlBaseMat = new THREE.MeshStandardMaterial({ color: 0x6e7d8d, roughness: 0.7 });
    this.mlBase = new THREE.Mesh(mlBaseGeo, mlBaseMat);
    this.mlBase.position.set(0, 9, 0);
    this.mlBase.castShadow = true;
    this.padGroup.add(this.mlBase);

    // Mobile Launcher 1 Tower (Red Lattice Truss)
    this.mlTower = new THREE.Group();
    const towerHeight = 115;
    const towerTrussMat = new THREE.MeshStandardMaterial({ color: 0xb53526, roughness: 0.6 });
    for (let h = 0; h < towerHeight; h += 8) {
      const ringGeo = new THREE.BoxGeometry(10, 0.8, 10);
      const ring = new THREE.Mesh(ringGeo, towerTrussMat);
      ring.position.set(16, 14 + h, 0);
      this.mlTower.add(ring);
    }
    // 4 vertical tower columns
    for (let dx of [-4.5, 4.5]) {
      for (let dz of [-4.5, 4.5]) {
        const colGeo = new THREE.CylinderGeometry(0.5, 0.5, towerHeight, 6);
        const col = new THREE.Mesh(colGeo, towerTrussMat);
        col.position.set(16 + dx, 14 + towerHeight / 2, dz);
        this.mlTower.add(col);
      }
    }
    // Crew Access Arm (CAA) at 90m level
    const caaGeo = new THREE.BoxGeometry(16, 2.5, 2.5);
    const caaMat = new THREE.MeshStandardMaterial({ color: 0xdde2e8, roughness: 0.5 });
    this.caaArm = new THREE.Mesh(caaGeo, caaMat);
    this.caaArm.position.set(8, 88, 0);
    this.mlTower.add(this.caaArm);

    this.padGroup.add(this.mlTower);

    // 2. SLS Block 1 Vehicle
    this.vehicle = new THREE.Group();
    this.vehicle.position.set(0, 14, 0);
    this.scene.add(this.vehicle);

    // A. Core Stage (Orange Foam external cylinder)
    // Scale: height = 64.6m, diameter = 8.4m -> radius = 4.2m
    const coreGeo = new THREE.CylinderGeometry(4.2, 4.2, 60, 32);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0xc96428, // Sourced external tank orange insulation
      roughness: 0.75,
      metalness: 0.15
    });
    this.coreStage = new THREE.Mesh(coreGeo, coreMat);
    this.coreStage.position.y = 30;
    this.coreStage.castShadow = true;
    this.vehicle.add(this.coreStage);

    // Intertank Ribbed Thrust Structure Ring
    const intertankGeo = new THREE.CylinderGeometry(4.25, 4.25, 6, 32);
    const intertankMat = new THREE.MeshStandardMaterial({ color: 0xa84e18, roughness: 0.6 });
    const intertank = new THREE.Mesh(intertankGeo, intertankMat);
    intertank.position.y = 35;
    this.coreStage.add(intertank);

    // Core Stage Aft Engine Boat-tail (4x RS-25)
    this.rs25Engines = new THREE.Group();
    this.coreStage.add(this.rs25Engines);
    const engMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.8, roughness: 0.3 });
    const engCoords = [
      [-1.8, -30, -1.8],
      [1.8, -30, -1.8],
      [-1.8, -30, 1.8],
      [1.8, -30, 1.8]
    ];
    for (let c of engCoords) {
      const bellGeo = new THREE.ConeGeometry(0.9, 2.4, 16, 1, true);
      const bell = new THREE.Mesh(bellGeo, engMat);
      bell.position.set(c[0], c[1], c[2]);
      bell.rotation.x = Math.PI;
      this.rs25Engines.add(bell);
    }

    // B. Twin Five-Segment Solid Rocket Boosters (SRBs)
    // Scale: height = 53.9m, diameter = 3.7m -> radius = 1.85m
    this.srbGroup = new THREE.Group();
    this.vehicle.add(this.srbGroup);

    const srbMat = new THREE.MeshStandardMaterial({
      color: 0xf2f4f7, // Sourced white thermal paint
      roughness: 0.4,
      metalness: 0.2
    });
    const srbNoseMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.5 });

    this.srbLeft = new THREE.Group();
    this.srbRight = new THREE.Group();
    this.srbLeft.position.set(-6.5, 27, 0);
    this.srbRight.position.set(6.5, 27, 0);

    for (let srb of [this.srbLeft, this.srbRight]) {
      // Booster main cylinder
      const cylGeo = new THREE.CylinderGeometry(1.85, 1.85, 48, 24);
      const cyl = new THREE.Mesh(cylGeo, srbMat);
      cyl.castShadow = true;
      srb.add(cyl);

      // 5-segment joint rings
      for (let j = -18; j <= 18; j += 9) {
        const jointGeo = new THREE.TorusGeometry(1.9, 0.08, 8, 24);
        const joint = new THREE.Mesh(jointGeo, srbNoseMat);
        joint.rotation.x = Math.PI / 2;
        joint.position.y = j;
        srb.add(joint);
      }

      // Forward aerodynamic nose cone
      const noseGeo = new THREE.ConeGeometry(1.85, 6, 24);
      const nose = new THREE.Mesh(noseGeo, srbMat);
      nose.position.y = 27;
      srb.add(nose);

      // Canted exhaust nozzle
      const nozzleGeo = new THREE.ConeGeometry(1.4, 2.8, 16, 1, true);
      const nozzle = new THREE.Mesh(nozzleGeo, engMat);
      nozzle.position.y = -25.4;
      nozzle.rotation.x = Math.PI;
      srb.add(nozzle);
    }
    this.srbGroup.add(this.srbLeft);
    this.srbGroup.add(this.srbRight);

    // C. Interim Cryogenic Propulsion Stage (ICPS) & LVSA
    this.icpsGroup = new THREE.Group();
    this.icpsGroup.position.set(0, 64, 0);
    this.vehicle.add(this.icpsGroup);

    // Launch Vehicle Stage Adapter (conical adapter from 8.4m to 5m)
    const lvsaGeo = new THREE.CylinderGeometry(2.5, 4.2, 5.5, 32);
    const lvsaMat = new THREE.MeshStandardMaterial({ color: 0x9e5225, roughness: 0.6 });
    const lvsa = new THREE.Mesh(lvsaGeo, lvsaMat);
    this.icpsGroup.add(lvsa);

    // ICPS Hydrogen tank cylinder
    const icpsTankGeo = new THREE.CylinderGeometry(2.5, 2.5, 8, 32);
    const icpsTankMat = new THREE.MeshStandardMaterial({ color: 0xefefef, roughness: 0.35 });
    const icpsTank = new THREE.Mesh(icpsTankGeo, icpsTankMat);
    icpsTank.position.y = 6.75;
    this.icpsGroup.add(icpsTank);

    // D. Orion MPCV (Crew Module CM-003 + European Service Module ESM-2)
    this.orionGroup = new THREE.Group();
    this.orionGroup.position.set(0, 76, 0);
    this.vehicle.add(this.orionGroup);

    // ESM Service Module Cylinder
    const esmGeo = new THREE.CylinderGeometry(2.5, 2.5, 4, 32);
    const esmMat = new THREE.MeshStandardMaterial({ color: 0xd9e0e8, metalness: 0.5, roughness: 0.3 });
    this.esm = new THREE.Mesh(esmGeo, esmMat);
    this.orionGroup.add(this.esm);

    // Orion Crew Module Cone (5m base diameter)
    const cmGeo = new THREE.ConeGeometry(2.5, 3.3, 32);
    const cmMat = new THREE.MeshStandardMaterial({
      color: 0x30343a, // Thermal protective tile black/charcoal
      roughness: 0.3,
      metalness: 0.4
    });
    this.cm = new THREE.Mesh(cmGeo, cmMat);
    this.cm.position.y = 3.65;
    this.orionGroup.add(this.cm);

    // E. Launch Abort System (LAS) Tower & Fairings
    this.lasGroup = new THREE.Group();
    this.lasGroup.position.set(0, 81.5, 0);
    this.vehicle.add(this.lasGroup);

    // Fairing cover skirt
    const fairingGeo = new THREE.CylinderGeometry(1.2, 2.5, 3.5, 24);
    const fairingMat = new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.4 });
    const fairing = new THREE.Mesh(fairingGeo, fairingMat);
    this.lasGroup.add(fairing);

    // Abort motor tower column
    const abortTowerGeo = new THREE.CylinderGeometry(0.7, 0.7, 10, 16);
    const abortTower = new THREE.Mesh(abortTowerGeo, fairingMat);
    abortTower.position.y = 6.75;
    this.lasGroup.add(abortTower);

    // Nose cone with steer thrusters
    const lasNoseGeo = new THREE.ConeGeometry(0.7, 2.5, 16);
    const lasNose = new THREE.Mesh(lasNoseGeo, srbNoseMat);
    lasNose.position.y = 13.0;
    this.lasGroup.add(lasNose);

    // 3. Dynamic Particle Plumes
    this.buildPlumes();
  }

  buildPlumes() {
    this.plumeGroup = new THREE.Group();
    this.vehicle.add(this.plumeGroup);

    // SRB Exhaust Plumes (Bright orange flame cones)
    const srbPlumeGeo = new THREE.ConeGeometry(3.5, 25, 20, 1, true);
    const srbPlumeMat = new THREE.MeshBasicMaterial({
      color: 0xff6600,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide
    });

    this.srbPlumeL = new THREE.Mesh(srbPlumeGeo, srbPlumeMat);
    this.srbPlumeL.position.set(-6.5, 0, 0);
    this.srbPlumeR = new THREE.Mesh(srbPlumeGeo, srbPlumeMat);
    this.srbPlumeR.position.set(6.5, 0, 0);
    this.plumeGroup.add(this.srbPlumeL);
    this.plumeGroup.add(this.srbPlumeR);

    // RS-25 Core Plume (Pale cyan / shock core)
    const corePlumeGeo = new THREE.ConeGeometry(3.8, 18, 20, 1, true);
    const corePlumeMat = new THREE.MeshBasicMaterial({
      color: 0x44bbff,
      transparent: true,
      opacity: 0.7,
      side: THREE.DoubleSide
    });
    this.corePlume = new THREE.Mesh(corePlumeGeo, corePlumeMat);
    this.corePlume.position.set(0, -6, 0);
    this.plumeGroup.add(this.corePlume);

    // Set initial plume scale to zero (unignited)
    this.setPlumeActive(false);
  }

  setPlumeActive(active, srbActive = true, coreActive = true) {
    if (!active) {
      if (this.srbPlumeL) this.srbPlumeL.visible = false;
      if (this.srbPlumeR) this.srbPlumeR.visible = false;
      if (this.corePlume) this.corePlume.visible = false;
      if (this.plumeLight) this.plumeLight.intensity = 0;
      return;
    }
    if (this.srbPlumeL) this.srbPlumeL.visible = srbActive;
    if (this.srbPlumeR) this.srbPlumeR.visible = srbActive;
    if (this.corePlume) this.corePlume.visible = coreActive;
    if (this.plumeLight) this.plumeLight.intensity = srbActive ? 3.5 : 1.2;
  }

  setSceneMode(mode) {
    this.sceneMode = mode;
    this.resetVehicleOffsets();

    if (mode === 'parts' || mode === 'assembly') {
      // 1. Assembly / Exploded Hardware Layout
      this.padGroup.visible = false;
      this.vehicle.position.set(0, 0, 0);
      this.srbLeft.position.set(-25, 27, 0);
      this.srbRight.position.set(25, 27, 0);
      this.coreStage.position.set(0, 20, 0);
      this.icpsGroup.position.set(0, 65, 0);
      this.orionGroup.position.set(0, 85, 0);
      this.lasGroup.position.set(0, 105, 0);
      this.setPlumeActive(false);
      this.camera.position.set(0, 60, 180);
      if (this.controls) this.controls.target.set(0, 50, 0);
    } else if (mode === 'pad_countdown' || mode === 'pad_ready') {
      // 2. Pad & Countdown
      this.padGroup.visible = true;
      this.mlTower.visible = true;
      this.caaArm.rotation.y = 0; // Connected to Orion
      this.vehicle.position.set(0, 14, 0);
      this.setPlumeActive(false);
      this.camera.position.set(135, 65, 145);
      if (this.controls) this.controls.target.set(0, 52, 0);
    } else if (mode === 'liftoff') {
      // 3. Liftoff (Active initial ascent: MET 48s, plume active)
      this.padGroup.visible = true;
      this.mlTower.visible = true;
      this.caaArm.rotation.y = Math.PI / 3; // Retracted
      this.vehicle.position.set(0, 24, 0);
      this.setPlumeActive(true, true, true);
      this.camera.position.set(140, 72, 160);
      if (this.controls) this.controls.target.set(0, 58, 0);
    } else if (mode === 'ascent') {
      // 4. Ascent
      this.padGroup.visible = true;
      this.mlTower.visible = true;
      this.caaArm.rotation.y = Math.PI / 3;
      this.vehicle.position.set(0, 85, 0);
      this.setPlumeActive(true, true, true);
      this.camera.position.set(80, 110, 100);
      if (this.controls) this.controls.target.set(0, 85, 0);
    } else if (mode === 'booster_sep') {
      // 5. Booster Separation
      this.padGroup.visible = false;
      this.vehicle.position.set(0, 120, 0);
      this.srbLeft.position.set(-22, 10, 0);
      this.srbRight.position.set(22, 10, 0);
      this.srbLeft.rotation.z = 0.35;
      this.srbRight.rotation.z = -0.35;
      this.lasGroup.visible = true;
      this.setPlumeActive(true, false, true); // Core only
      this.camera.position.set(0, 130, 140);
      if (this.controls) this.controls.target.set(0, 120, 0);
    } else if (mode === 'core_sep') {
      // 6. Core Stage Separation
      this.padGroup.visible = false;
      this.vehicle.position.set(0, 150, 0);
      this.srbGroup.visible = false;
      this.lasGroup.visible = false;
      this.coreStage.position.set(0, -30, 0);
      this.icpsGroup.position.set(0, 64, 0);
      this.orionGroup.position.set(0, 76, 0);
      this.setPlumeActive(false);
      this.camera.position.set(40, 160, 80);
      if (this.controls) this.controls.target.set(0, 150, 0);
    } else if (mode === 'orion_icps') {
      // 7. Orion / ICPS In-Orbit
      this.padGroup.visible = false;
      this.coreStage.visible = false;
      this.srbGroup.visible = false;
      this.lasGroup.visible = false;
      this.icpsGroup.visible = true;
      this.orionGroup.visible = true;
      this.vehicle.position.set(0, 50, 0);
      this.setPlumeActive(false);
      this.camera.position.set(30, 60, 50);
      if (this.controls) this.controls.target.set(0, 50, 0);
    } else if (mode === 'tli') {
      // 8. TLI Burn (ESM OMS-E firing)
      this.padGroup.visible = false;
      this.coreStage.visible = false;
      this.srbGroup.visible = false;
      this.lasGroup.visible = false;
      this.icpsGroup.visible = false;
      this.orionGroup.visible = true;
      this.vehicle.position.set(0, 40, 0);
      this.setPlumeActive(false);
      this.camera.position.set(-35, 50, 45);
      if (this.controls) this.controls.target.set(0, 40, 0);
    } else {
      // Default flight
      this.padGroup.visible = true;
      this.mlTower.visible = true;
      this.caaArm.rotation.y = Math.PI / 3;
      if (this.controls) this.controls.target.set(0, 45, 0);
    }
  }

  setCameraPreset(preset) {
    if (!this.controls) return;
    if (preset === 'Launch View' || preset === 'launch_view') {
      this.camera.position.set(110, 55, 125);
      this.controls.target.set(0, 35, 0);
    } else if (preset === 'Follow Vehicle' || preset === 'follow') {
      this.camera.position.set(this.vehicle.position.x + 40, this.vehicle.position.y + 20, this.vehicle.position.z + 50);
      this.controls.target.copy(this.vehicle.position);
    } else if (preset === 'Earth View' || preset === 'earth') {
      this.camera.position.set(0, 350, 400);
      this.controls.target.set(0, 0, 0);
    } else if (preset === 'Moon View' || preset === 'moon') {
      this.camera.position.set(200, 150, -200);
      this.controls.target.set(0, 40, 0);
    }
  }

  resetVehicleOffsets() {
    this.coreStage.visible = true;
    this.srbGroup.visible = true;
    this.srbLeft.position.set(-6.5, 27, 0);
    this.srbRight.position.set(6.5, 27, 0);
    this.srbLeft.rotation.set(0, 0, 0);
    this.srbRight.rotation.set(0, 0, 0);
    this.icpsGroup.visible = true;
    this.orionGroup.visible = true;
    this.lasGroup.visible = true;
    this.coreStage.position.set(0, 30, 0);
    this.icpsGroup.position.set(0, 64, 0);
    this.orionGroup.position.set(0, 76, 0);
    this.lasGroup.position.set(0, 81.5, 0);
  }

  updateTelemetry(pkt) {
    if (!pkt) return;
    this.altitude_km = pkt.trajectory ? pkt.trajectory.altitude_km : (pkt.alt_km || 0.0);
    this.velocity_m_s = pkt.trajectory ? pkt.trajectory.velocity_m_s : (pkt.vel_m_s || 0.0);
    this.mach = pkt.trajectory ? (pkt.trajectory.mach || 0.0) : (pkt.mach || 0.0);
    this.stage = pkt.mission_stage || pkt.stage || 'SLS_ASCENT_LEO';
    this.met_s = pkt.met_real_sec || pkt.met_s || 0.0;

    if (this.sceneMode !== 'flight') return;

    // Numerical Flight Visual Updates
    const isAscent = this.met_s < 494.0;
    this.padGroup.visible = this.altitude_km < 35.0;

    if (this.met_s <= 0.0) {
      this.vehicle.position.set(0, 14, 0);
      this.setPlumeActive(false);
    } else if (this.met_s < 129.0) {
      // First Stage: Core + 2x SRBs
      const visualY = 14 + Math.min(250.0, this.altitude_km * 3.5);
      this.vehicle.position.set(0, visualY, 0);
      this.setPlumeActive(true, true, true);
      this.srbGroup.visible = true;
      this.lasGroup.visible = true;
    } else if (this.met_s < 193.0) {
      // SRB Separation: SRBs push outward and fall behind
      const visualY = 14 + Math.min(350.0, this.altitude_km * 2.8);
      this.vehicle.position.set(0, visualY, 0);
      this.setPlumeActive(true, false, true);

      // Animate SRB lateral drift
      const dt_sep = this.met_s - 129.0;
      this.srbLeft.position.x = -6.5 - dt_sep * 1.8;
      this.srbLeft.position.y = 27 - dt_sep * 3.5;
      this.srbRight.position.x = 6.5 + dt_sep * 1.8;
      this.srbRight.position.y = 27 - dt_sep * 3.5;
      this.srbGroup.visible = dt_sep < 25.0;
      this.lasGroup.visible = true;
    } else if (this.met_s < 482.0) {
      // Core Stage Post-LAS Jettison
      const visualY = 14 + Math.min(500.0, this.altitude_km * 2.0);
      this.vehicle.position.set(0, visualY, 0);
      this.setPlumeActive(true, false, true);
      this.srbGroup.visible = false;
      this.lasGroup.visible = false;
    } else {
      // MECO & Core Separation: Stack is ICPS + Orion
      this.setPlumeActive(false);
      this.coreStage.visible = false;
      this.srbGroup.visible = false;
      this.lasGroup.visible = false;
      this.icpsGroup.visible = true;
      this.orionGroup.visible = true;
    }

    // Follow camera in flight
    if (this.controls && isAscent && this.met_s > 0) {
      this.controls.target.y = this.vehicle.position.y + 25;
      this.camera.position.y = this.vehicle.position.y + 40;
    }
  }

  animate() {
    requestAnimationFrame(this.animate);
    if (this.controls) this.controls.update();

    // Plume flicker effect
    if (this.srbPlumeL.visible) {
      const flicker = 0.95 + Math.random() * 0.12;
      this.srbPlumeL.scale.set(flicker, flicker * (1.0 + Math.random() * 0.15), flicker);
      this.srbPlumeR.scale.set(flicker, flicker * (1.0 + Math.random() * 0.15), flicker);
      this.corePlume.scale.set(flicker * 0.9, flicker, flicker * 0.9);
    }

    this.renderer.render(this.scene, this.camera);
  }
}

window.SLSLaunchViewer3D = SLSLaunchViewer3D;
