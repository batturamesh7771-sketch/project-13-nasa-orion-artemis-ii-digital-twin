/**
 * NASA Orion Artemis II Digital Twin — Master 3D Mission Engine
 * Authoritative Unified 3D Simulation across all 8 Official Artemis II Mission Phases:
 *
 *   AIM 1: SLS Block 1 Launch & Pad LC-39B (Earth Surface, Florida Coastline, Mobile Launcher 1)
 *          - Sourced Florida sunny daytime atmosphere (blue sky, horizon fog, daylight sunlight)
 *          - Merritt Island water lagoon & reflection, shoreline vegetation, concrete apron
 *          - Mobile Launcher 1 (ML-1) platform with American flag banner & 115m umbilical tower
 *          - SLS Block 1 liftoff from launch mount, 4x RS-25 + 2x SRB plumes, staging separations
 *
 *   AIM 2: Earth-Moon Mission Trajectory (Earth on Left, Moon on Right, 100% matching NASA Profile)
 *          - Blue Marble Earth at (-42, -2, 0) with cyan Rayleigh scattering halo
 *          - Cratered Moon at (56, 12, -6)
 *          - 4 Distinct Trajectory Tracks exactly from Orbit3D:
 *              1. Outbound Translunar Coast: Solid Cyan curve with forward green arrowheads
 *              2. Circum-Lunar Flyby: Electric Blue arc swinging behind Moon far side
 *              3. Trans-Earth Return Coast: Yellow dashed curve with Earthward yellow arrowheads
 *              4. Skip Reentry: Green curve entering Earth with Pacific Ocean splashdown beacon
 *          - In-situ Orion Spacecraft STRICTLY LOCKED TO TRAJECTORY:
 *              * Position copied directly from curve point (zero floating, zero miscrossing)
 *              * Quaternion aligned to tangent velocity vector (prograde, zero random rotation)
 *              * 4x X-wing photovoltaic solar arrays in authentic dihedral X-formation
 *          - Canonical Overview Camera at (10, 18, 175) framing Earth-Moon horizontally
 *
 *   AIM 3: Reentry, Parachutes, Pacific Ocean Splashdown & Navy Recovery
 *          - Hypersonic Skip Reentry (EI-400, 25,000 MPH) with glowing Avcoat ablator & bow shock
 *          - 3x 116-ft NASA Ring-Sail Canopies (alternating orange/white 24-gore pattern)
 *          - Pacific Ocean water plane with 5x orange CMUS uprighting bags & yellow flotation collar
 *          - USS Portland (LPD 27) amphibious transport dock & Navy RHIB boat on recovery scene
 */

class ArtemisMasterMission3D {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.warn('ArtemisMasterMission3D: Canvas not found:', canvasId);
      return;
    }

    this.container = this.canvas.parentElement;
    this.currentMet = 0.0;
    this.cameraMode = 'auto'; // 'auto', 'chase', 'pad', 'earth', 'moon', 'reentry', 'ocean'
    this.simTime = 0.0;

    // Geometry layout constants matching NASA Earth-Moon reference frame
    this.earthPos = new THREE.Vector3(-42, -2, 0);
    this.moonPos = new THREE.Vector3(56, 12, -6);
    this.earthRadius = 17.0;
    this.moonRadius = 5.0;

    this._initThree();
    this._initLighting();
    this._buildEnvironment();
    this._buildLaunchPadAndSLS();
    this._buildTrajectory();
    this._buildInSituOrion();
    this._buildReentryAndRecovery();
    this._buildCockpitInterior();

    window.addEventListener('resize', () => this.onResize());
    this._animate = this._animate.bind(this);
    requestAnimationFrame(this._animate);
  }

  // =========================================================================
  // 1. Core WebGL Renderer & Perspective Camera
  // =========================================================================
  _initThree() {
    const w = this.container ? this.container.clientWidth : (this.canvas.clientWidth || 1200);
    const h = this.container ? this.container.clientHeight : (this.canvas.clientHeight || 540);

    this.scene = new THREE.Scene();

    // Default to Florida daytime blue sky for Launch Pad
    this.skyColorDay = new THREE.Color(0x3878b4);
    this.skyColorSpace = new THREE.Color(0x02050c);
    this.scene.background = this.skyColorDay;
    this.scene.fog = new THREE.FogExp2(0x78a8d0, 0.001);

    this.camera = new THREE.PerspectiveCamera(38, w / Math.max(h, 1), 0.5, 4000);
    this.camera.position.set(120, 68, 140);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.maxDistance = 2500;
      this.controls.minDistance = 2.0;
      this.controls.target.set(0, 56, 0);
    }
  }

  onResize() {
    if (!this.canvas || !this.container) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    if (w <= 0 || h <= 0) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  // =========================================================================
  // 2. Dynamic Lighting Rig
  // =========================================================================
  _initLighting() {
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
    this.scene.add(this.ambientLight);

    // Primary Sun Light
    this.sunLight = new THREE.DirectionalLight(0xfffbf0, 2.2);
    this.sunLight.position.set(220, 260, 180);
    this.sunLight.castShadow = true;
    this.scene.add(this.sunLight);

    // Earthshine / Sky bounce light
    this.skyLight = new THREE.DirectionalLight(0x64b5f6, 0.55);
    this.skyLight.position.set(-180, 80, -120);
    this.scene.add(this.skyLight);

    // Rocket Plume Point Light
    this.flameLight = new THREE.PointLight(0xff7700, 0.0, 200);
    this.flameLight.position.set(0, 0, 0);
    this.scene.add(this.flameLight);

    // Pacific Daylight Hemisphere for Reentry/Splashdown
    this.marineHemi = new THREE.HemisphereLight(0x90caf9, 0x0d47a1, 0.85);
    this.marineHemi.visible = false;
    this.scene.add(this.marineHemi);
  }

  // =========================================================================
  // 3. Deep Space Environment: Earth, Moon & Starfield
  // =========================================================================
  _buildEnvironment() {
    // A. Multi-Spectral Starfield (Shown in Space phases)
    const starCount = 2000;
    const starGeo = new THREE.BufferGeometry();
    const starPos = new Float32Array(starCount * 3);
    const starColors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 1400 + Math.random() * 800;
      starPos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      starPos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      starPos[i * 3 + 2] = r * Math.cos(phi);

      const tint = Math.random();
      if (tint < 0.65) {
        starColors[i * 3] = 1.0; starColors[i * 3 + 1] = 1.0; starColors[i * 3 + 2] = 1.0;
      } else if (tint < 0.85) {
        starColors[i * 3] = 0.65; starColors[i * 3 + 1] = 0.85; starColors[i * 3 + 2] = 1.0;
      } else {
        starColors[i * 3] = 1.0; starColors[i * 3 + 1] = 0.85; starColors[i * 3 + 2] = 0.65;
      }
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));
    this.starfield = new THREE.Points(starGeo, new THREE.PointsMaterial({ size: 2.2, vertexColors: true, transparent: true, opacity: 0.85 }));
    this.starfield.visible = false;
    this.scene.add(this.starfield);

    // B. Earth Globe (Positioned at -42, -2, 0 matching Orbit3D)
    this.earthGroup = new THREE.Group();
    this.earthGroup.position.copy(this.earthPos);

    const textureLoader = new THREE.TextureLoader();
    const earthTex = textureLoader.load('/static/textures/earth_map.png');
    earthTex.colorSpace = THREE.SRGBColorSpace;

    const earthGeo = new THREE.SphereGeometry(this.earthRadius, 64, 48);
    const earthMat = new THREE.MeshStandardMaterial({
      map: earthTex,
      roughness: 0.75,
      metalness: 0.10
    });
    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthMesh.rotation.y = 1.2;
    this.earthGroup.add(this.earthMesh);

    // Glowing Atmospheric Rim Halo
    const atmosGeo = new THREE.SphereGeometry(this.earthRadius + 0.9, 36, 36);
    const atmosMat = new THREE.MeshBasicMaterial({
      color: 0x48cae4,
      transparent: true,
      opacity: 0.22,
      side: THREE.BackSide
    });
    this.atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
    this.earthGroup.add(this.atmosMesh);

    // DSN (Deep Space Network) 70-meter Ground Station Antennas
    this.dsnStations = [];
    const buildDSNStation = (name, lat, lon, code) => {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lon + 180) * (Math.PI / 180);
      const r = this.earthRadius + 0.12;
      const x = -(r * Math.sin(phi) * Math.cos(theta));
      const z = (r * Math.sin(phi) * Math.sin(theta));
      const y = (r * Math.cos(phi));

      const siteGroup = new THREE.Group();
      siteGroup.position.set(x, y, z);
      siteGroup.lookAt(x * 2, y * 2, z * 2);

      // Concrete Pedestal
      const baseMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.45, 0.35, 8), new THREE.MeshStandardMaterial({ color: 0x8899aa, metalness: 0.5 }));
      baseMesh.rotation.x = Math.PI / 2;
      siteGroup.add(baseMesh);

      // 70m Parabolic Dish
      const dishGeo = new THREE.SphereGeometry(0.75, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.42);
      const dishMat = new THREE.MeshStandardMaterial({ color: 0xddeeff, roughness: 0.3, metalness: 0.7, side: THREE.DoubleSide });
      const dishMesh = new THREE.Mesh(dishGeo, dishMat);
      dishMesh.position.z = 0.35;
      dishMesh.rotation.x = Math.PI;

      // Sub-reflector tripod
      const tripodGeo = new THREE.ConeGeometry(0.12, 0.45, 4);
      const tripodMesh = new THREE.Mesh(tripodGeo, new THREE.MeshBasicMaterial({ color: 0x00e5ff }));
      tripodMesh.position.z = 0.55;
      dishMesh.add(tripodMesh);

      siteGroup.add(dishMesh);
      this.earthMesh.add(siteGroup);

      return { name, code, lat, lon, group: siteGroup, dish: dishMesh };
    };

    this.dsnGoldstone = buildDSNStation('Goldstone (DSS-14)', 35.4266, -116.89, 'GDS');
    this.dsnMadrid = buildDSNStation('Madrid (DSS-63)', 40.4314, -4.248, 'MAD');
    this.dsnCanberra = buildDSNStation('Canberra (DSS-43)', -35.4014, 148.9817, 'CAN');
    this.dsnStations = [this.dsnGoldstone, this.dsnMadrid, this.dsnCanberra];

    // Pulsing Microwave DSN Comm Beam Line
    const beamGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, 0)
    ]);
    this.dsnBeamLine = new THREE.Line(beamGeo, new THREE.LineBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.75
    }));
    this.scene.add(this.dsnBeamLine);

    this.earthGroup.visible = false;
    this.scene.add(this.earthGroup);

    // C. Moon Globe (NASA CGI Moon Kit SVS 4720 High-Res LRO + LOLA Elevation)
    this.moonGroup = new THREE.Group();
    this.moonGroup.position.copy(this.moonPos);
    // Accurate Moon axial tilt 1.543 deg relative to ecliptic normal
    this.moonGroup.rotation.z = 1.543 * (Math.PI / 180.0);

    const lroColorTex = textureLoader.load('/static/assets/textures/moon/lroc_color.jpg', undefined, undefined, () => {
      return textureLoader.load('/static/textures/moon_map.png');
    });
    lroColorTex.colorSpace = THREE.SRGBColorSpace;
    const lolaBumpTex = textureLoader.load('/static/assets/textures/moon/lola_bump.jpg');

    const moonGeo = new THREE.SphereGeometry(this.moonRadius, 128, 128);
    const moonMat = new THREE.MeshStandardMaterial({
      map: lroColorTex,
      bumpMap: lolaBumpTex,
      bumpScale: 0.18,
      roughness: 0.88,
      metalness: 0.02
    });
    this.moonMesh = new THREE.Mesh(moonGeo, moonMat);
    this.moonGroup.add(this.moonMesh);

    this.moonGroup.visible = false;
    this.scene.add(this.moonGroup);
  }

  // =========================================================================
  // 4. Florida Launch Pad LC-39B & Detailed SLS Block 1 Vehicle
  // =========================================================================
  _buildLaunchPadAndSLS() {
    this.padTerrainGroup = new THREE.Group();

    // 1. Florida Merritt Island Terrain & Water Lagoon (Matching Real Photos)
    // Water Lagoon (Foreground reflective water)
    const waterGeo = new THREE.PlaneGeometry(1600, 1600, 16, 16);
    const waterMat = new THREE.MeshStandardMaterial({
      color: 0x1b4468, // Deep blue Florida coastal water
      roughness: 0.25,
      metalness: 0.35
    });
    const water = new THREE.Mesh(waterGeo, waterMat);
    water.rotation.x = -Math.PI / 2;
    water.position.y = -3.0;
    this.padTerrainGroup.add(water);

    // Shoreline & Merritt Island Green Grass
    const shoreGeo = new THREE.PlaneGeometry(900, 600);
    const shoreMat = new THREE.MeshStandardMaterial({
      color: 0x2e5c38, // Florida coastal vegetation green
      roughness: 0.90,
      metalness: 0.05
    });
    const shore = new THREE.Mesh(shoreGeo, shoreMat);
    shore.rotation.x = -Math.PI / 2;
    shore.position.set(0, -1.5, -150);
    this.padTerrainGroup.add(shore);

    // Concrete Pad LC-39B Hardstand Octagonal Mound
    const padBaseGeo = new THREE.CylinderGeometry(75, 95, 7, 8);
    const padBaseMat = new THREE.MeshStandardMaterial({ color: 0x4d5b68, roughness: 0.85 });
    const padBase = new THREE.Mesh(padBaseGeo, padBaseMat);
    padBase.position.set(0, 1.5, 0);
    padBase.receiveShadow = true;
    this.padTerrainGroup.add(padBase);

    // 2. Mobile Launcher 1 (ML-1) Platform
    const mlBaseGeo = new THREE.BoxGeometry(45, 10, 40);
    const mlBaseMat = new THREE.MeshStandardMaterial({ color: 0x6e7d8d, roughness: 0.70 });
    this.mlBase = new THREE.Mesh(mlBaseGeo, mlBaseMat);
    this.mlBase.position.set(0, 9.0, 0);
    this.mlBase.castShadow = true;
    this.padTerrainGroup.add(this.mlBase);

    // American Flag Banner on ML-1 Platform (Matching Real Photo)
    const flagGeo = new THREE.PlaneGeometry(18, 9.5);
    const flagCanvas = document.createElement('canvas');
    flagCanvas.width = 512; flagCanvas.height = 256;
    const fctx = flagCanvas.getContext('2d');
    fctx.fillStyle = '#b22234'; fctx.fillRect(0, 0, 512, 256);
    const stripeH = 256 / 13;
    fctx.fillStyle = '#ffffff';
    for (let s = 1; s < 13; s += 2) fctx.fillRect(0, s * stripeH, 512, stripeH);
    fctx.fillStyle = '#3c3b6e'; fctx.fillRect(0, 0, 200, 7 * stripeH);
    const flagTex = new THREE.CanvasTexture(flagCanvas);
    const flagMesh = new THREE.Mesh(flagGeo, new THREE.MeshBasicMaterial({ map: flagTex }));
    flagMesh.position.set(0, 9.0, 20.2);
    this.padTerrainGroup.add(flagMesh);

    // 3. Mobile Launcher Umbilical Tower (115m Steel Lattice Truss)
    this.mlTower = new THREE.Group();
    const towerH = 115;
    const towerMat = new THREE.MeshStandardMaterial({ color: 0x8a382e, roughness: 0.65 }); // Classic steel red-gray
    for (let h = 0; h < towerH; h += 8) {
      const ring = new THREE.Mesh(new THREE.BoxGeometry(11, 0.9, 11), towerMat);
      ring.position.set(16, 14 + h, 0);
      this.mlTower.add(ring);
    }
    for (let dx of [-5, 5]) {
      for (let dz of [-5, 5]) {
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, towerH, 6), towerMat);
        col.position.set(16 + dx, 14 + towerH / 2, dz);
        this.mlTower.add(col);
      }
    }

    // Crew Access Arm (CAA) at 88m level
    const caaMesh = new THREE.Mesh(new THREE.BoxGeometry(16, 2.8, 2.8), new THREE.MeshStandardMaterial({ color: 0xe0e6ed, roughness: 0.4 }));
    caaMesh.position.set(8, 88, 0);
    this.mlTower.add(caaMesh);
    // Environmental Clean Room at end of arm
    const cleanRoom = new THREE.Mesh(new THREE.BoxGeometry(4.5, 4.0, 4.0), new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.3 }));
    cleanRoom.position.set(0.5, 88.5, 0);
    this.mlTower.add(cleanRoom);

    // Lightning Protection Mast on top of tower
    const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.8, 24, 8), new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 0.8 }));
    mast.position.set(16, 14 + towerH + 12, 0);
    this.mlTower.add(mast);

    this.padTerrainGroup.add(this.mlTower);
    this.scene.add(this.padTerrainGroup);

    // 4. SLS Block 1 Vehicle
    this.slsGroup = new THREE.Group();
    this.slsGroup.position.set(0, 14, 0);

    const coreMat = new THREE.MeshStandardMaterial({ color: 0xc96428, roughness: 0.75, metalness: 0.15 }); // Authentic SOFI orange foam
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xf4f6f8, roughness: 0.35, metalness: 0.20 });
    const darkMetalMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.55, metalness: 0.70 });

    // Core Stage Cylinder (60m high, 8.4m diameter)
    const coreCylGeo = new THREE.CylinderGeometry(4.2, 4.2, 60, 32);
    this.coreStage = new THREE.Mesh(coreCylGeo, coreMat);
    this.coreStage.position.y = 30;
    this.coreStage.castShadow = true;
    this.slsGroup.add(this.coreStage);

    // Intertank Ring
    const intertank = new THREE.Mesh(new THREE.CylinderGeometry(4.25, 4.25, 6, 32), new THREE.MeshStandardMaterial({ color: 0xa84e18, roughness: 0.6 }));
    intertank.position.y = 35;
    this.coreStage.add(intertank);

    // Forward Skirt
    const forwardSkirt = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.2, 7, 32), whiteMat);
    forwardSkirt.position.y = 59.5;
    this.coreStage.add(forwardSkirt);

    // 4x RS-25 Core Engines
    const nozzleOffsets = [[-1.5, -30.5, -1.5], [1.5, -30.5, -1.5], [-1.5, -30.5, 1.5], [1.5, -30.5, 1.5]];
    nozzleOffsets.forEach(pos => {
      const nozzle = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.95, 2.8, 16), darkMetalMat);
      nozzle.position.set(pos[0], pos[1], pos[2]);
      this.coreStage.add(nozzle);
    });

    // 2x Five-Segment Solid Rocket Boosters (SRBs)
    this.srbGroup = new THREE.Group();
    const buildSRB = (isRight) => {
      const srb = new THREE.Group();
      const srbCasing = new THREE.Mesh(new THREE.CylinderGeometry(1.85, 1.85, 50, 24), whiteMat);
      srbCasing.castShadow = true;
      srb.add(srbCasing);

      const srbNose = new THREE.Mesh(new THREE.ConeGeometry(1.85, 6.5, 24), whiteMat);
      srbNose.position.y = 28.2;
      srb.add(srbNose);

      const srbSkirt = new THREE.Mesh(new THREE.CylinderGeometry(1.85, 2.2, 4.2, 24), darkMetalMat);
      srbSkirt.position.y = -27.1;
      srb.add(srbSkirt);

      srb.position.set(isRight ? 6.5 : -6.5, 28, 0);
      return srb;
    };
    this.srbLeft = buildSRB(false);
    this.srbRight = buildSRB(true);
    this.srbGroup.add(this.srbLeft);
    this.srbGroup.add(this.srbRight);
    this.slsGroup.add(this.srbGroup);

    // ICPS Stage & Orion Stack
    this.icpsGroup = new THREE.Group();
    const icps = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.6, 9.0, 32), whiteMat);
    icps.position.y = 71.5;
    this.icpsGroup.add(icps);
    this.slsGroup.add(this.icpsGroup);

    this.slsOrion = new THREE.Group();
    this.slsOrion.position.set(0, 78, 0);
    const esm = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.2, 4.5, 32), whiteMat);
    this.slsOrion.add(esm);
    const cm = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 3.3, 3.8, 32), new THREE.MeshStandardMaterial({ color: 0x1f2428, roughness: 0.3 }));
    cm.position.y = 4.0;
    this.slsOrion.add(cm);

    // LAS Tower
    this.lasTower = new THREE.Group();
    const lasJacket = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 1.4, 6.5, 16), whiteMat);
    lasJacket.position.y = 9.2;
    this.lasTower.add(lasJacket);
    const lasMotor = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 8.5, 16), whiteMat);
    lasMotor.position.y = 16.5;
    this.lasTower.add(lasMotor);
    const lasNose = new THREE.Mesh(new THREE.ConeGeometry(0.5, 3.0, 16), whiteMat);
    lasNose.position.y = 22.2;
    this.lasTower.add(lasNose);
    this.slsOrion.add(this.lasTower);
    this.slsGroup.add(this.slsOrion);

    // Dynamic Rocket Plumes
    this.plumeGroup = new THREE.Group();
    const plumeMat = new THREE.MeshBasicMaterial({ color: 0xff6600, transparent: true, opacity: 0.85 });
    this.corePlume = new THREE.Mesh(new THREE.ConeGeometry(3.8, 28, 16), plumeMat);
    this.corePlume.position.y = -14;
    this.corePlume.rotation.x = Math.PI;
    this.plumeGroup.add(this.corePlume);

    const srbPlumeMat = new THREE.MeshBasicMaterial({ color: 0xffaa00, transparent: true, opacity: 0.90 });
    this.srbPlumeL = new THREE.Mesh(new THREE.ConeGeometry(2.4, 24, 16), srbPlumeMat);
    this.srbPlumeL.position.set(-6.5, -12, 0);
    this.srbPlumeL.rotation.x = Math.PI;
    this.plumeGroup.add(this.srbPlumeL);
    this.srbPlumeR = new THREE.Mesh(new THREE.ConeGeometry(2.4, 24, 16), srbPlumeMat);
    this.srbPlumeR.position.set(6.5, -12, 0);
    this.srbPlumeR.rotation.x = Math.PI;
    this.plumeGroup.add(this.srbPlumeR);

    this.plumeGroup.visible = false;
    this.slsGroup.add(this.plumeGroup);
    this.scene.add(this.slsGroup);
  }

  // =========================================================================
  // 5. Authoritative Earth-Moon Trajectory Curves (100% Matching Orbit3D)
  // =========================================================================
  _buildTrajectory() {
    this.trajGroup = new THREE.Group();

    // 1. OUTBOUND TRANSLUNAR COAST (Solid Cyan line with forward directional arrows)
    this.outboundCurve = new THREE.CubicBezierCurve3(
      new THREE.Vector3(this.earthPos.x + 8, this.earthPos.y + 12, 0),
      new THREE.Vector3(-10, 26, 0),
      new THREE.Vector3(30, 20, -5),
      new THREE.Vector3(this.moonPos.x - 2, this.moonPos.y + 7, -6)
    );
    const outPts = this.outboundCurve.getPoints(80);
    const outGeom = new THREE.BufferGeometry().setFromPoints(outPts);
    this.outboundLine = new THREE.Line(outGeom, new THREE.LineBasicMaterial({ color: 0x00e5ff, linewidth: 2.5 }));
    this.trajGroup.add(this.outboundLine);

    // Outbound directional arrow cones pointing forward to Moon
    const arrowGeom = new THREE.ConeGeometry(0.8, 2.2, 8);
    const arrowMat = new THREE.MeshBasicMaterial({ color: 0x00e676 });
    [0.25, 0.65].forEach(t => {
      const pt = this.outboundCurve.getPoint(t);
      const tangent = this.outboundCurve.getTangent(t).normalize();
      const arrow = new THREE.Mesh(arrowGeom, arrowMat);
      arrow.position.copy(pt);
      arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      this.trajGroup.add(arrow);
    });

    // 2. LUNAR FLYBY PERICYNTHION LOOP (Electric Blue arc swinging behind Moon far side)
    this.flybySpline = new THREE.CatmullRomCurve3([
      new THREE.Vector3(this.moonPos.x - 2, this.moonPos.y + 7, -6),
      new THREE.Vector3(this.moonPos.x + 8, this.moonPos.y + 6, -7),
      new THREE.Vector3(this.moonPos.x + 12, this.moonPos.y, -6),
      new THREE.Vector3(this.moonPos.x + 8, this.moonPos.y - 6, -5),
      new THREE.Vector3(this.moonPos.x - 3, this.moonPos.y - 6, -6)
    ]);
    const flybyPts = this.flybySpline.getPoints(60);
    this.flybyLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(flybyPts), new THREE.LineBasicMaterial({ color: 0x0084ff, linewidth: 2.5 }));
    this.trajGroup.add(this.flybyLine);

    // 3. INBOUND RETURN TRAJECTORY (Yellow dashed curve returning to Earth)
    this.returnCurve = new THREE.CubicBezierCurve3(
      new THREE.Vector3(this.moonPos.x - 3, this.moonPos.y - 6, -6),
      new THREE.Vector3(32, -14, -5),
      new THREE.Vector3(0, -22, -2),
      new THREE.Vector3(this.earthPos.x + 8, this.earthPos.y - 10, 0)
    );
    const inPts = this.returnCurve.getPoints(80);
    const inGeom = new THREE.BufferGeometry().setFromPoints(inPts);
    this.inboundLine = new THREE.Line(inGeom, new THREE.LineDashedMaterial({
      color: 0xffd600,
      dashSize: 3.5,
      gapSize: 2.0,
      linewidth: 2
    }));
    this.inboundLine.computeLineDistances();
    this.trajGroup.add(this.inboundLine);

    // Inbound directional arrow cones pointing to Earth
    const retArrowMat = new THREE.MeshBasicMaterial({ color: 0xffd600 });
    [0.35, 0.75].forEach(t => {
      const pt = this.returnCurve.getPoint(t);
      const tangent = this.returnCurve.getTangent(t).normalize();
      const arrow = new THREE.Mesh(arrowGeom, retArrowMat);
      arrow.position.copy(pt);
      arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      this.trajGroup.add(arrow);
    });

    // 4. ATMOSPHERIC SKIP REENTRY & SPLASHDOWN (Atmospheric arc curving into Pacific)
    this.reentryCurve = new THREE.CubicBezierCurve3(
      new THREE.Vector3(this.earthPos.x + 8, this.earthPos.y - 10, 0),
      new THREE.Vector3(this.earthPos.x + 4, this.earthPos.y - 6, 0),
      new THREE.Vector3(this.earthPos.x + 3, this.earthPos.y + 2, 0),
      new THREE.Vector3(this.earthPos.x + 5, this.earthPos.y + 6, 0)
    );
    const rePts = this.reentryCurve.getPoints(30);
    this.reentryLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(rePts), new THREE.LineBasicMaterial({ color: 0x00e676, linewidth: 2.5 }));
    this.trajGroup.add(this.reentryLine);

    // Pacific Splashdown Beacon Ring
    const splashBeacon = new THREE.Mesh(new THREE.RingGeometry(0.8, 1.4, 16), new THREE.MeshBasicMaterial({ color: 0x00e676, side: THREE.DoubleSide }));
    splashBeacon.position.copy(new THREE.Vector3(this.earthPos.x + 5, this.earthPos.y + 6, 0));
    this.trajGroup.add(splashBeacon);

    this.trajGroup.visible = false;
    this.scene.add(this.trajGroup);
  }

  // =========================================================================
  // 6. In-Situ Orion MPCV (Oriented along +X for Flawless Trajectory Tracking)
  // High-Fidelity Geometry, NASA Worm Decals, PBR Solar Panels & Dynamic OMS Plume
  // =========================================================================
  _buildInSituOrion() {
    this.insituOrionGroup = new THREE.Group();

    // 1. Procedural Orion Capsule Texture (NASA Worm Logo, Meatball, US Flag, Windows)
    const cmCanvas = document.createElement('canvas');
    cmCanvas.width = 512; cmCanvas.height = 256;
    const cctx = cmCanvas.getContext('2d');
    // White/silver thermal blanket background
    cctx.fillStyle = '#e8ecf2';
    cctx.fillRect(0, 0, 512, 256);
    // Thermal blanket stitching seams
    cctx.strokeStyle = '#c5ccd6';
    cctx.lineWidth = 1;
    for (let y = 20; y < 256; y += 30) {
      cctx.beginPath(); cctx.moveTo(0, y); cctx.lineTo(512, y); cctx.stroke();
    }
    for (let x = 30; x < 512; x += 45) {
      cctx.beginPath(); cctx.moveTo(x, 0); cctx.lineTo(x, 256); cctx.stroke();
    }
    // Iconic Red NASA Worm Logo
    cctx.fillStyle = '#ff1122';
    cctx.font = 'bold 34px sans-serif';
    cctx.fillText('NASA', 80, 140);
    cctx.fillText('NASA', 340, 140);
    // United States Flag Decal
    cctx.fillStyle = '#b22234';
    cctx.fillRect(190, 115, 36, 22);
    cctx.fillStyle = '#ffffff';
    cctx.fillRect(190, 119, 36, 4);
    cctx.fillRect(190, 127, 36, 4);
    cctx.fillStyle = '#3c3b6e';
    cctx.fillRect(190, 115, 16, 12);
    // Cockpit Windows (Twin dark trapezoids)
    cctx.fillStyle = '#0a192f';
    cctx.fillRect(100, 50, 42, 24);
    cctx.fillRect(150, 50, 42, 24);

    const cmTex = new THREE.CanvasTexture(cmCanvas);
    const cmMat = new THREE.MeshStandardMaterial({
      map: cmTex,
      roughness: 0.32,
      metalness: 0.68
    });

    // Conical Crew Module (Apex pointing in +X direction)
    const cmGeom = new THREE.ConeGeometry(1.65, 2.15, 32);
    this.insituCM = new THREE.Mesh(cmGeom, cmMat);
    this.insituCM.rotation.z = -Math.PI / 2; // Nose pointing along +X
    this.insituOrionGroup.add(this.insituCM);

    // Forward Docking Hatch Tunnel on apex (X = +1.15)
    const hatchMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.38, 0.44, 0.45, 16),
      new THREE.MeshStandardMaterial({ color: 0x3a424a, metalness: 0.85, roughness: 0.25 })
    );
    hatchMesh.rotation.z = Math.PI / 2;
    hatchMesh.position.set(1.15, 0, 0);
    this.insituOrionGroup.add(hatchMesh);

    // 4x CM Reaction Control System (RCS) Pitch/Roll Thruster Pods
    const rcsMat = new THREE.MeshStandardMaterial({ color: 0x1a202c, metalness: 0.8 });
    for (let r = 0; r < 4; r++) {
      const rAng = (r * Math.PI) / 2;
      const rcsPod = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.14, 0.28, 8), rcsMat);
      rcsPod.position.set(-0.65, Math.sin(rAng) * 1.55, Math.cos(rAng) * 1.55);
      rcsPod.rotation.x = rAng;
      this.insituOrionGroup.add(rcsPod);
    }

    // Heat Shield on CM base (Spherical segment)
    const hsGeom = new THREE.SphereGeometry(1.68, 24, 12, 0, Math.PI * 2, 0, Math.PI * 0.35);
    const hsMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.92, metalness: 0.1 });
    const hs = new THREE.Mesh(hsGeom, hsMat);
    hs.rotation.z = Math.PI / 2;
    hs.position.set(-1.02, 0, 0);
    this.insituOrionGroup.add(hs);

    // 2. European Service Module (ESM)
    this.insituESM = new THREE.Group();

    // Cylindrical ESM Body with radiator panel stripes
    const smCanvas = document.createElement('canvas');
    smCanvas.width = 512; smCanvas.height = 256;
    const sctx = smCanvas.getContext('2d');
    sctx.fillStyle = '#ffffff';
    sctx.fillRect(0, 0, 512, 256);
    // Vertical radiator cooling fins & panels
    sctx.fillStyle = '#dbe4ee';
    for (let x = 10; x < 512; x += 22) {
      sctx.fillRect(x, 15, 14, 226);
    }
    // ESA Blue emblem
    sctx.fillStyle = '#003247';
    sctx.font = 'bold 22px sans-serif';
    sctx.fillText('esa', 60, 135);
    sctx.fillText('esa', 320, 135);
    const smTex = new THREE.CanvasTexture(smCanvas);

    const smMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(1.52, 1.52, 2.3, 32),
      new THREE.MeshStandardMaterial({ map: smTex, roughness: 0.40, metalness: 0.45 })
    );
    smMesh.position.set(-1.95, 0, 0);
    smMesh.rotation.z = Math.PI / 2;
    this.insituESM.add(smMesh);

    // Gold MLI (Multilayer Insulation) Aft Bulkhead
    const mliMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37, // Metallic gold
      metalness: 0.90,
      roughness: 0.20
    });
    const aftBulkhead = new THREE.Mesh(new THREE.CircleGeometry(1.48, 24), mliMat);
    aftBulkhead.position.set(-3.11, 0, 0);
    aftBulkhead.rotation.y = -Math.PI / 2;
    this.insituESM.add(aftBulkhead);

    // AJ10-190 Main Engine Gimballed Titanium Nozzle
    const omsMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.32, 0.82, 1.35, 24),
      new THREE.MeshStandardMaterial({ color: 0x27272a, roughness: 0.45, metalness: 0.88 })
    );
    omsMesh.position.set(-3.55, 0, 0);
    omsMesh.rotation.z = Math.PI / 2;
    this.insituESM.add(omsMesh);

    // 4x ESM RCS Quad Blocks (4 x 4 = 16 attitude control nozzles)
    this.insituRcsPlumes = [];
    for (let q = 0; q < 4; q++) {
      const qAng = (q * Math.PI) / 2 + Math.PI / 4;
      const qBlock = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.35, 0.35), rcsMat);
      qBlock.position.set(-2.4, Math.sin(qAng) * 1.58, Math.cos(qAng) * 1.58);
      this.insituESM.add(qBlock);

      // Micro RCS exhaust bursts
      const rcsPlume = new THREE.Mesh(
        new THREE.ConeGeometry(0.12, 0.45, 8),
        new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.0 })
      );
      rcsPlume.position.set(-2.4, Math.sin(qAng) * 1.85, Math.cos(qAng) * 1.85);
      rcsPlume.rotation.z = Math.PI / 2;
      this.insituESM.add(rcsPlume);
      this.insituRcsPlumes.push(rcsPlume);
    }

    // 3. 4x Solar Array Wings in authentic Dihedral Canted X-Formation (19m wingspan)
    const solarCanvas = document.createElement('canvas');
    solarCanvas.width = 128; solarCanvas.height = 512;
    const solCtx = solarCanvas.getContext('2d');
    solCtx.fillStyle = '#0b1d3a'; // Deep space dark blue
    solCtx.fillRect(0, 0, 128, 512);
    // Photovoltaic cell grid
    solCtx.strokeStyle = '#1e90ff';
    solCtx.lineWidth = 1;
    for (let sy = 10; sy < 512; sy += 18) {
      solCtx.beginPath(); solCtx.moveTo(4, sy); solCtx.lineTo(124, sy); solCtx.stroke();
    }
    for (let sx = 10; sx < 128; sx += 20) {
      solCtx.beginPath(); solCtx.moveTo(sx, 4); solCtx.lineTo(sx, 508); solCtx.stroke();
    }
    // Silver busbar collectors
    solCtx.strokeStyle = '#c0d6f2';
    solCtx.lineWidth = 2;
    solCtx.beginPath(); solCtx.moveTo(64, 4); solCtx.lineTo(64, 508); solCtx.stroke();

    const solarTex = new THREE.CanvasTexture(solarCanvas);
    const solarMat = new THREE.MeshStandardMaterial({
      map: solarTex,
      roughness: 0.22,
      metalness: 0.82,
      emissive: 0x001833
    });
    const wingGeom = new THREE.BoxGeometry(0.48, 4.2, 0.08);

    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI / 2) + Math.PI / 4;
      const wingArm = new THREE.Group();
      wingArm.position.set(-1.95, 0, 0);

      const wing = new THREE.Mesh(wingGeom, solarMat);
      wing.position.set(0, Math.sin(angle) * 3.1, Math.cos(angle) * 3.1);
      wing.rotation.x = angle;
      // Authentic +15° forward dihedral cant matching NASA Orion CAD
      wing.rotation.y = 0.22;
      wingArm.add(wing);

      // Gold hinge gimbal
      const hinge = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.35, 12), mliMat);
      hinge.position.set(0, Math.sin(angle) * 1.55, Math.cos(angle) * 1.55);
      hinge.rotation.x = angle;
      wingArm.add(hinge);

      this.insituESM.add(wingArm);
    }

    // 4. Dynamic Fiery OMS Main Engine Plume (TLI Burn, Pericynthion Flyby & Return Burns)
    this.insituOmsPlumeGroup = new THREE.Group();
    this.insituOmsPlumeGroup.position.set(-4.2, 0, 0);

    // Inner Supersonic Incandescent Core Flame Cone (Cyan/White)
    const coreFlameGeo = new THREE.ConeGeometry(0.68, 4.5, 24, 1, true);
    this.insituCoreFlameMat = new THREE.MeshBasicMaterial({
      color: 0xa0f5ff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    this.insituCoreFlame = new THREE.Mesh(coreFlameGeo, this.insituCoreFlameMat);
    this.insituCoreFlame.rotation.z = Math.PI / 2; // Expelling backwards along -X
    this.insituOmsPlumeGroup.add(this.insituCoreFlame);

    // Outer Hypergolic Expansion Mantle (Electric Blue/Violet Aerozine-50 / NTO)
    const mantleFlameGeo = new THREE.ConeGeometry(1.35, 7.2, 24, 1, true);
    this.insituMantleFlameMat = new THREE.MeshBasicMaterial({
      color: 0x0088ff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    this.insituMantleFlame = new THREE.Mesh(mantleFlameGeo, this.insituMantleFlameMat);
    this.insituMantleFlame.rotation.z = Math.PI / 2;
    this.insituOmsPlumeGroup.add(this.insituMantleFlame);

    // Shock Diamonds (3 luminous discs spaced along core)
    this.insituShockDiamonds = [];
    for (let d = 0; d < 3; d++) {
      const sDiam = new THREE.Mesh(
        new THREE.RingGeometry(0.05, 0.42 - d * 0.08, 16),
        new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.0, side: THREE.DoubleSide, blending: THREE.AdditiveBlending })
      );
      sDiam.position.set(-1.2 - d * 1.1, 0, 0);
      sDiam.rotation.y = Math.PI / 2;
      this.insituOmsPlumeGroup.add(sDiam);
      this.insituShockDiamonds.push(sDiam);
    }

    // Trailing Combustion Particle Sparks
    const flameSparkCount = 45;
    const flameSparkGeo = new THREE.BufferGeometry();
    const flameSparkPos = new Float32Array(flameSparkCount * 3);
    for (let s = 0; s < flameSparkCount; s++) {
      flameSparkPos[s * 3] = -Math.random() * 8.5;
      flameSparkPos[s * 3 + 1] = (Math.random() - 0.5) * 1.2;
      flameSparkPos[s * 3 + 2] = (Math.random() - 0.5) * 1.2;
    }
    flameSparkGeo.setAttribute('position', new THREE.BufferAttribute(flameSparkPos, 3));
    this.insituSparkMat = new THREE.PointsMaterial({
      color: 0x80d8ff,
      size: 2.2,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending
    });
    this.insituFlameParticles = new THREE.Points(flameSparkGeo, this.insituSparkMat);
    this.insituOmsPlumeGroup.add(this.insituFlameParticles);

    this.insituESM.add(this.insituOmsPlumeGroup);
    this.insituOrionGroup.add(this.insituESM);

    this.insituOrionGroup.visible = false;
    this.scene.add(this.insituOrionGroup);
  }

  // =========================================================================
  // 7. Trajectory Point & Tangent Evaluator (Zero Floating / Zero Miscrossing)
  // =========================================================================
  getMissionPositionAndTangent(tFrac) {
    const f = Math.max(0, Math.min(1.0, tFrac));

    if (f < 0.05) {
      // Phase 1 & 2: Launch & Earth Orbit Insertion
      const u = f / 0.05;
      const angle = Math.PI * 0.95 + u * Math.PI * 0.65;
      const r = this.earthRadius + 2.5;
      const pos = new THREE.Vector3(
        this.earthPos.x + r * Math.cos(angle),
        this.earthPos.y + r * Math.sin(angle),
        0
      );
      const tangent = new THREE.Vector3(-Math.sin(angle), Math.cos(angle), 0).normalize();
      return { pos, tangent, stage: 'EARTH_ORBIT', esmAttached: true };
    } else if (f < 0.44) {
      // Phase 3 & 4: Outbound Translunar Coast (TLI Burn to Moon)
      const u = (f - 0.05) / (0.44 - 0.05);
      const pos = this.outboundCurve.getPoint(u);
      const tangent = this.outboundCurve.getTangent(u).normalize();
      return { pos, tangent, stage: 'TRANSLUNAR_COAST', esmAttached: true };
    } else if (f < 0.54) {
      // Phase 5: Lunar Flyby (Behind Moon far side)
      const u = (f - 0.44) / (0.54 - 0.44);
      const pos = this.flybySpline.getPoint(u);
      const tangent = this.flybySpline.getTangent(u).normalize();
      return { pos, tangent, stage: 'LUNAR_FLYBY', esmAttached: true };
    } else if (f < 0.94) {
      // Phase 6: Trans-Earth Return Trajectory (Free Return coast to Earth)
      const u = (f - 0.54) / (0.94 - 0.54);
      const pos = this.returnCurve.getPoint(u);
      const tangent = this.returnCurve.getTangent(u).normalize();
      const esmAttached = (u < 0.96);
      return { pos, tangent, stage: 'TRANS_EARTH_RETURN', esmAttached };
    } else {
      // Phase 7 & 8: Atmospheric Reentry & Splashdown
      const u = (f - 0.94) / (1.0 - 0.94);
      const pos = this.reentryCurve.getPoint(u);
      const tangent = this.reentryCurve.getTangent(u).normalize();
      return { pos, tangent, stage: 'REENTRY_SPLASHDOWN', esmAttached: false };
    }
  }

  // =========================================================================
  // 8. Reentry Hypersonic Shock, Parachutes, Pacific Ocean & Recovery
  // =========================================================================
  _buildReentryAndRecovery() {
    this.reentryGroup = new THREE.Group();

    // 1. Orion Crew Module (5.02m conical capsule with thermal protection tiles)
    this.reentryCapsule = new THREE.Group();
    const cmGeo = new THREE.CylinderGeometry(0.85, 2.52, 2.65, 32);
    const cmMat = new THREE.MeshStandardMaterial({
      color: 0x1f2428,
      roughness: 0.40,
      metalness: 0.60
    });
    this.cmBodyMesh = new THREE.Mesh(cmGeo, cmMat);
    this.cmBodyMesh.position.y = 1.32;
    this.reentryCapsule.add(this.cmBodyMesh);

    // Trapezoidal Cockpit Windows with optical reflective glass
    const winMat = new THREE.MeshStandardMaterial({
      color: 0x88d4f7,
      roughness: 0.15,
      metalness: 0.90,
      emissive: 0x112233
    });
    for (let s of [-0.48, 0.48]) {
      const win = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.38, 0.08), winMat);
      win.position.set(s, 2.0, 1.48);
      win.rotation.x = -0.32;
      this.reentryCapsule.add(win);
    }

    // Reaction Control System (RCS) roll/pitch thruster pods
    const rcsMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.8 });
    for (let a = 0; a < 4; a++) {
      const ang = (a * Math.PI) / 2;
      const pod = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 0.35, 12), rcsMat);
      pod.position.set(Math.cos(ang) * 2.2, 0.9, Math.sin(ang) * 2.2);
      pod.rotation.z = Math.PI / 2;
      this.reentryCapsule.add(pod);
    }

    // Detachable Forward Bay Cover (FBC) with apex docking cone
    this.reentryFBC = new THREE.Group();
    const fbcNose = new THREE.Mesh(new THREE.ConeGeometry(0.88, 0.85, 32), cmMat);
    fbcNose.position.y = 3.08;
    this.reentryFBC.add(fbcNose);
    const fbcBeacon = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.25, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    fbcBeacon.position.y = 3.55;
    this.reentryFBC.add(fbcBeacon);
    this.reentryCapsule.add(this.reentryFBC);

    // Procedural Avcoat Charred Heat Shield Tile Texture (Matching Real Photo 4)
    this.hsCanvas = document.createElement('canvas');
    this.hsCanvas.width = 512; this.hsCanvas.height = 512;
    this.hctx = this.hsCanvas.getContext('2d');
    this._renderColdHeatShieldTexture();

    this.hsTexture = new THREE.CanvasTexture(this.hsCanvas);
    const hsMat = new THREE.MeshStandardMaterial({
      map: this.hsTexture,
      roughness: 0.92,
      metalness: 0.08,
      emissive: new THREE.Color(0xff4500),
      emissiveIntensity: 0.0
    });
    this.heatShieldMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.55, 2.48, 0.42, 32), hsMat);
    this.heatShieldMesh.position.y = -0.18;
    this.reentryCapsule.add(this.heatShieldMesh);

    // Radiant Thermal Point Light emitted by 5,000°F Avcoat Heat Shield
    this.reentryHeatLight = new THREE.PointLight(0xff5500, 0.0, 45);
    this.reentryHeatLight.position.set(0, -0.6, 0);
    this.reentryCapsule.add(this.reentryHeatLight);

    // 2. European Service Module (ESM) & Catastrophic Incineration Debris
    this.reentryESMGroup = new THREE.Group();
    const esmCyl = new THREE.Mesh(new THREE.CylinderGeometry(2.45, 2.45, 2.4, 24), new THREE.MeshStandardMaterial({ color: 0xf5f7fa, roughness: 0.4, metalness: 0.3 }));
    esmCyl.position.y = -1.5;
    this.reentryESMGroup.add(esmCyl);
    const esmOms = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.75, 1.2, 16), new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8 }));
    esmOms.position.y = -2.9;
    this.reentryESMGroup.add(esmOms);

    // 4 Solar Array Wings in X-formation
    const esmSolarMat = new THREE.MeshStandardMaterial({ color: 0x0066cc, roughness: 0.25, metalness: 0.85, emissive: 0x001a33 });
    for (let i = 0; i < 4; i++) {
      const ang = (i * Math.PI) / 2 + Math.PI / 4;
      const wing = new THREE.Mesh(new THREE.BoxGeometry(0.35, 3.8, 0.08), esmSolarMat);
      wing.position.set(Math.cos(ang) * 3.4, -1.5, Math.sin(ang) * 3.4);
      wing.rotation.y = ang;
      this.reentryESMGroup.add(wing);
    }
    this.reentryGroup.add(this.reentryESMGroup);

    // ESM Burning Debris Group (Disintegrating fragments & trailing fire streaks)
    this.esmDebrisGroup = new THREE.Group();
    this.esmFragments = [];
    const debrisMat = new THREE.MeshBasicMaterial({ color: 0xff6600 });
    for (let d = 0; d < 12; d++) {
      const frag = new THREE.Mesh(new THREE.BoxGeometry(0.6 + Math.random() * 0.8, 0.4 + Math.random() * 0.6, 0.3 + Math.random() * 0.5), debrisMat);
      frag.position.set((Math.random() - 0.5) * 6, -Math.random() * 8, (Math.random() - 0.5) * 6);
      this.esmDebrisGroup.add(frag);
      this.esmFragments.push(frag);
    }
    this.esmDebrisGroup.visible = false;
    this.reentryGroup.add(this.esmDebrisGroup);

    // 3. Hypervelocity Shock Wave & Luminous Plasma Sheath
    this.plasmaShockGroup = new THREE.Group();

    // Curved Stagnation Bow Shock Cone
    const bowGeo = new THREE.ConeGeometry(4.4, 2.6, 32, 1, true);
    this.plasmaBowMat = new THREE.MeshBasicMaterial({
      color: 0xffdfba,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    this.plasmaBowCone = new THREE.Mesh(bowGeo, this.plasmaBowMat);
    this.plasmaBowCone.position.y = -0.55;
    this.plasmaShockGroup.add(this.plasmaBowCone);

    // Outer Ionization Sheath wrapping the Capsule
    const sheathGeo = new THREE.CylinderGeometry(1.6, 3.4, 4.0, 24, 1, true);
    this.plasmaSheathMat = new THREE.MeshBasicMaterial({
      color: 0xff6600,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    this.plasmaSheath = new THREE.Mesh(sheathGeo, this.plasmaSheathMat);
    this.plasmaSheath.position.y = 1.2;
    this.plasmaShockGroup.add(this.plasmaSheath);

    // Long Supersonic Ionization Wake Sheath
    const wakeGeo = new THREE.CylinderGeometry(5.2, 3.2, 30.0, 24, 1, true);
    this.plasmaWakeMat = new THREE.MeshBasicMaterial({
      color: 0xff8800,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    this.plasmaWakeCone = new THREE.Mesh(wakeGeo, this.plasmaWakeMat);
    this.plasmaWakeCone.position.y = 16.5;
    this.plasmaShockGroup.add(this.plasmaWakeCone);

    // Ablation Spark Particle System (Spalling incandescent Avcoat char particles)
    const sparkCount = 250;
    const sparkGeo = new THREE.BufferGeometry();
    this.sparkPositions = new Float32Array(sparkCount * 3);
    for (let i = 0; i < sparkCount; i++) {
      this.sparkPositions[i * 3] = (Math.random() - 0.5) * 4.5;
      this.sparkPositions[i * 3 + 1] = Math.random() * 26.0;
      this.sparkPositions[i * 3 + 2] = (Math.random() - 0.5) * 4.5;
    }
    sparkGeo.setAttribute('position', new THREE.BufferAttribute(this.sparkPositions, 3));
    this.sparkMat = new THREE.PointsMaterial({
      color: 0xffaa00,
      size: 2.2,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending
    });
    this.ablationParticles = new THREE.Points(sparkGeo, this.sparkMat);
    this.plasmaShockGroup.add(this.ablationParticles);

    this.reentryCapsule.add(this.plasmaShockGroup);

    // 4. 2x High-Altitude Conical Drogue Parachutes (25,000 ft / 7.6 km)
    this.drogueGroup = new THREE.Group();
    const drogueCanvas = document.createElement('canvas');
    drogueCanvas.width = 256; drogueCanvas.height = 128;
    const dctx = drogueCanvas.getContext('2d');
    const dGores = 12; const dW = 256 / dGores;
    for (let g = 0; g < dGores; g++) {
      dctx.fillStyle = (g % 2 === 0) ? '#ff4d00' : '#ffffff';
      dctx.fillRect(g * dW, 0, dW, 128);
    }
    const drogueTex = new THREE.CanvasTexture(drogueCanvas);
    const drogueMat = new THREE.MeshStandardMaterial({ map: drogueTex, roughness: 0.85, side: THREE.DoubleSide });

    const drogueOffsets = [[-1.2, 16.0, -0.8], [1.2, 16.0, 0.8]];
    this.drogueCanopies = [];
    drogueOffsets.forEach(pos => {
      const dCanopy = new THREE.Mesh(new THREE.ConeGeometry(1.65, 2.8, 16, 1, true), drogueMat);
      dCanopy.position.set(pos[0], pos[1], pos[2]);
      dCanopy.rotation.x = Math.PI;
      this.drogueGroup.add(dCanopy);
      this.drogueCanopies.push(dCanopy);

      const dLineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 2.6, 0),
        new THREE.Vector3(pos[0], pos[1] - 1.4, pos[2])
      ]);
      this.drogueGroup.add(new THREE.Line(dLineGeo, new THREE.LineBasicMaterial({ color: 0xcccccc })));
    });
    this.drogueGroup.visible = false;
    this.reentryCapsule.add(this.drogueGroup);

    // 5. 3x Giant 116-ft NASA Ring-Sail Main Parachutes (9,500 ft / 2.9 km)
    this.mainChuteGroup = new THREE.Group();
    const mainCanvas = document.createElement('canvas');
    mainCanvas.width = 512; mainCanvas.height = 256;
    const mctx = mainCanvas.getContext('2d');
    const mGores = 24; const mW = 512 / mGores;
    for (let g = 0; g < mGores; g++) {
      mctx.fillStyle = (g % 2 === 0) ? '#ff4d00' : '#ffffff';
      mctx.fillRect(g * mW, 0, mW, 256);
      // Circumferential aerodynamic ring-sail vent slots
      mctx.fillStyle = 'rgba(20, 25, 30, 0.45)';
      mctx.fillRect(g * mW, 110, mW, 14);
      mctx.fillRect(g * mW, 165, mW, 18);
    }
    const mainTex = new THREE.CanvasTexture(mainCanvas);
    const mainMat = new THREE.MeshStandardMaterial({ map: mainTex, roughness: 0.82, side: THREE.DoubleSide });

    const canopyOffsets = [
      [-4.5, 24.0, -2.6],
      [4.5, 24.0, -2.6],
      [0.0, 24.0, 4.5]
    ];
    this.mainCanopies = [];
    canopyOffsets.forEach((pos, idx) => {
      const cGroup = new THREE.Group();
      cGroup.position.set(pos[0], pos[1], pos[2]);

      const canopy = new THREE.Mesh(new THREE.SphereGeometry(4.6, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.58), mainMat);
      cGroup.add(canopy);
      this.mainCanopies.push(cGroup);
      this.mainChuteGroup.add(cGroup);

      // 8 authentic suspension lines per canopy drawn to forward bay confluence fitting
      const linePts = [];
      for (let l = 0; l < 8; l++) {
        const lang = (l * Math.PI * 2) / 8;
        linePts.push(new THREE.Vector3(0, 2.65, 0));
        linePts.push(new THREE.Vector3(pos[0] + Math.cos(lang) * 4.4, pos[1] - 0.4, pos[2] + Math.sin(lang) * 4.4));
      }
      const linesGeo = new THREE.BufferGeometry().setFromPoints(linePts);
      this.mainChuteGroup.add(new THREE.LineSegments(linesGeo, new THREE.LineBasicMaterial({ color: 0xeeeeee })));
    });
    this.mainChuteGroup.visible = false;
    this.reentryCapsule.add(this.mainChuteGroup);

    // 6. Splashdown Water Impact Plumes & Spray
    this.splashPlumeGroup = new THREE.Group();
    const splashCrown = new THREE.Mesh(
      new THREE.CylinderGeometry(6.5, 9.5, 4.5, 24, 1, true),
      new THREE.MeshBasicMaterial({ color: 0xd0ecff, transparent: true, opacity: 0.65, side: THREE.DoubleSide })
    );
    splashCrown.position.y = 2.2;
    this.splashPlumeGroup.add(splashCrown);

    // Water droplet spray particles
    const sprayCount = 150;
    const sprayGeo = new THREE.BufferGeometry();
    const sprayPos = new Float32Array(sprayCount * 3);
    for (let s = 0; s < sprayCount; s++) {
      sprayPos[s * 3] = (Math.random() - 0.5) * 14.0;
      sprayPos[s * 3 + 1] = Math.random() * 8.0;
      sprayPos[s * 3 + 2] = (Math.random() - 0.5) * 14.0;
    }
    sprayGeo.setAttribute('position', new THREE.BufferAttribute(sprayPos, 3));
    this.splashParticles = new THREE.Points(sprayGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 2.2, transparent: true, opacity: 0.75 }));
    this.splashPlumeGroup.add(this.splashParticles);
    this.splashPlumeGroup.visible = false;
    this.reentryGroup.add(this.splashPlumeGroup);

    // 7. Post-Splashdown Deflated / Collapsed Parachutes floating on Ocean
    this.collapsedCanopies = new THREE.Group();
    const colCanopyMat = new THREE.MeshStandardMaterial({ map: mainTex, roughness: 0.9, side: THREE.DoubleSide });
    for (let c = 0; c < 3; c++) {
      const cAng = (c * Math.PI * 2) / 3;
      const col = new THREE.Mesh(new THREE.CircleGeometry(4.2, 16), colCanopyMat);
      col.rotation.x = -Math.PI / 2;
      col.position.set(Math.cos(cAng) * 9.5, 0.04, Math.sin(cAng) * 9.5);
      this.collapsedCanopies.add(col);
    }
    this.collapsedCanopies.visible = false;
    this.reentryGroup.add(this.collapsedCanopies);

    // 8. 5x Bright Orange CMUS (Crew Module Uprighting System) Airbags
    this.cmusGroup = new THREE.Group();
    const cmusMat = new THREE.MeshStandardMaterial({ color: 0xff3d00, roughness: 0.35, metalness: 0.1 });
    for (let b = 0; b < 5; b++) {
      const bAng = (b * Math.PI * 2) / 5;
      const balloon = new THREE.Mesh(new THREE.SphereGeometry(0.48, 16, 12), cmusMat);
      balloon.scale.set(1.0, 1.35, 1.0);
      balloon.position.set(Math.cos(bAng) * 0.48, 2.85, Math.sin(bAng) * 0.48);
      this.cmusGroup.add(balloon);
    }
    this.cmusGroup.visible = false;
    this.reentryCapsule.add(this.cmusGroup);

    // 9. High-Visibility Neon Yellow-Green Flotation Collar
    this.collarMesh = new THREE.Mesh(
      new THREE.TorusGeometry(2.58, 0.35, 16, 48),
      new THREE.MeshStandardMaterial({ color: 0xbfff00, roughness: 0.45, metalness: 0.15 })
    );
    this.collarMesh.rotation.x = Math.PI / 2;
    this.collarMesh.position.y = 0.28;
    this.collarMesh.visible = false;
    this.reentryCapsule.add(this.collarMesh);

    this.reentryGroup.add(this.reentryCapsule);

    // 10. Photorealistic Procedural Rolling Pacific Ocean
    this.oceanGroup = new THREE.Group();
    this.oceanGeo = new THREE.PlaneGeometry(1200, 1200, 64, 64);
    const oceanMat = new THREE.MeshStandardMaterial({
      color: 0x0c4b78,
      roughness: 0.25,
      metalness: 0.45
    });
    this.oceanMesh = new THREE.Mesh(this.oceanGeo, oceanMat);
    this.oceanMesh.rotation.x = -Math.PI / 2;
    this.oceanMesh.receiveShadow = true;
    this.oceanGroup.add(this.oceanMesh);

    // 11. Navy Recovery Task Force: USS Portland (LPD 27) & 2x RHIB Boats
    this.recoveryFleetGroup = new THREE.Group();
    this.recoveryFleetGroup.visible = false;
    this.ussPortland = new THREE.Group();
    this.ussPortland.position.set(-110.0, 0.0, -130.0);

    const hazeGray = new THREE.MeshStandardMaterial({ color: 0x546e7a, roughness: 0.70 });
    const deckMat = new THREE.MeshStandardMaterial({ color: 0x37474f, roughness: 0.85 });

    // USS Portland 208m Hull
    const hullMesh = new THREE.Mesh(new THREE.BoxGeometry(14.0, 7.0, 55.0), hazeGray);
    hullMesh.position.y = 2.5;
    this.ussPortland.add(hullMesh);

    // Flight deck aft
    const flightDeck = new THREE.Mesh(new THREE.BoxGeometry(13.6, 0.5, 22.0), deckMat);
    flightDeck.position.set(0, 6.1, 15.0);
    this.ussPortland.add(flightDeck);

    // Superstructure & Bridge Island
    const island = new THREE.Mesh(new THREE.BoxGeometry(9.0, 7.5, 18.0), hazeGray);
    island.position.set(0, 7.2, -6.0);
    this.ussPortland.add(island);

    // Radar Mast & Antenna
    const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.8, 12.0, 8), hazeGray);
    mast.position.set(0, 16.0, -6.0);
    this.ussPortland.add(mast);

    this.recoveryFleetGroup.add(this.ussPortland);

    // 2x Navy Combat Rubber Raiding Craft / RHIB Inflatable Boats
    const buildRHIB = (x, z, rAng) => {
      const boat = new THREE.Group();
      boat.position.set(x, 0.15, z);
      boat.rotation.y = rAng;

      // Inflatable black rubber sponson collar
      const sponson = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.42, 12, 32), new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.8 }));
      sponson.rotation.x = Math.PI / 2;
      sponson.scale.set(0.65, 1.8, 0.65);
      boat.add(sponson);

      // Deck & console
      const bDeck = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.3, 3.8), new THREE.MeshStandardMaterial({ color: 0x37474f }));
      bDeck.position.y = 0.15;
      boat.add(bDeck);

      // 2 Navy rescue divers in black wetsuits
      for (let d of [-0.8, 0.8]) {
        const diver = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 1.1, 8), new THREE.MeshStandardMaterial({ color: 0x111111 }));
        diver.position.set(0, 0.75, d);
        boat.add(diver);
      }
      return boat;
    };

    this.rhib1 = buildRHIB(-6.8, 5.2, 0.45);
    this.rhib2 = buildRHIB(7.2, -4.8, -2.4);
    this.recoveryFleetGroup.add(this.rhib1);
    this.recoveryFleetGroup.add(this.rhib2);

    this.oceanGroup.add(this.recoveryFleetGroup);
    this.oceanGroup.visible = false;
    this.reentryGroup.add(this.oceanGroup);

    this.reentryGroup.visible = false;
    this.scene.add(this.reentryGroup);
  }

  // =========================================================================
  // 8B. Orion Crew Module Interior Cockpit & Dynamic Glass Displays (PFD)
  // =========================================================================
  _buildCockpitInterior() {
    this.cockpitGroup = new THREE.Group();

    // 1. Orion Pressure Vessel Cabin Shell
    const cabinGeo = new THREE.CylinderGeometry(2.3, 3.2, 3.0, 32, 4, true);
    const cabinMat = new THREE.MeshStandardMaterial({
      color: 0x161c26,
      roughness: 0.75,
      metalness: 0.45,
      side: THREE.BackSide
    });
    const cabinShell = new THREE.Mesh(cabinGeo, cabinMat);
    cabinShell.position.set(0, 1.0, 0);
    this.cockpitGroup.add(cabinShell);

    // Structural Ring Ribs
    for (let r = 0; r < 4; r++) {
      const ribGeo = new THREE.TorusGeometry(2.5 - r * 0.2, 0.05, 8, 32);
      const ribMat = new THREE.MeshStandardMaterial({ color: 0x2e3846, metalness: 0.6 });
      const rib = new THREE.Mesh(ribGeo, ribMat);
      rib.rotation.x = Math.PI / 2;
      rib.position.set(0, 0.2 + r * 0.7, 0);
      this.cockpitGroup.add(rib);
    }

    // 2. Forward Main Instrument Console Angled Toward Crew (20 deg tilt)
    const consoleGroup = new THREE.Group();
    consoleGroup.position.set(0, 0.95, -1.6);
    consoleGroup.rotation.x = 0.22;

    const panelGeo = new THREE.BoxGeometry(3.2, 1.1, 0.15);
    const panelMat = new THREE.MeshStandardMaterial({ color: 0x111620, roughness: 0.5, metalness: 0.8 });
    const panel = new THREE.Mesh(panelGeo, panelMat);
    consoleGroup.add(panel);

    // 3. 3x NASA DDU (Display & Control Unit) Glass Cockpit Screens
    // Screen 1 (Left - Commander PFD / ADI)
    this.pfdCanvas = document.createElement('canvas');
    this.pfdCanvas.width = 512; this.pfdCanvas.height = 512;
    this.pfdCtx = this.pfdCanvas.getContext('2d');
    this.pfdTexture = new THREE.CanvasTexture(this.pfdCanvas);
    const pfdMat = new THREE.MeshBasicMaterial({ map: this.pfdTexture });
    const pfdScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.75), pfdMat);
    pfdScreen.position.set(-1.0, 0.05, 0.08);
    consoleGroup.add(pfdScreen);

    // Screen 2 (Center - Orbital Navigation & Trajectory Map)
    this.navCanvas = document.createElement('canvas');
    this.navCanvas.width = 512; this.navCanvas.height = 512;
    this.navCtx = this.navCanvas.getContext('2d');
    this.navTexture = new THREE.CanvasTexture(this.navCanvas);
    const navMat = new THREE.MeshBasicMaterial({ map: this.navTexture });
    const navScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.75), navMat);
    navScreen.position.set(0.0, 0.05, 0.08);
    consoleGroup.add(navScreen);

    // Screen 3 (Right - Systems, ECLSS & Caution & Warning Matrix)
    this.sysCanvas = document.createElement('canvas');
    this.sysCanvas.width = 512; this.sysCanvas.height = 512;
    this.sysCtx = this.sysCanvas.getContext('2d');
    this.sysTexture = new THREE.CanvasTexture(this.sysCanvas);
    const sysMat = new THREE.MeshBasicMaterial({ map: this.sysTexture });
    const sysScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.75), sysMat);
    sysScreen.position.set(1.0, 0.05, 0.08);
    consoleGroup.add(sysScreen);

    // Screen Bezels
    const bezelMat = new THREE.MeshStandardMaterial({ color: 0x00e5ff, metalness: 0.8, roughness: 0.2 });
    [-1.0, 0.0, 1.0].forEach(x => {
      const bezel = new THREE.Mesh(new THREE.RingGeometry(0.42, 0.44, 4), bezelMat);
      bezel.position.set(x, 0.05, 0.081);
      consoleGroup.add(bezel);
    });

    // 4. Rotational Hand Controller (RHC)
    const rhcBase = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.2, 12), new THREE.MeshStandardMaterial({ color: 0x222222 }));
    rhcBase.position.set(-0.35, -0.2, 0.45);
    const rhcStick = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.28, 8), new THREE.MeshStandardMaterial({ color: 0x555555 }));
    rhcStick.position.set(-0.35, -0.05, 0.45);
    consoleGroup.add(rhcBase);
    consoleGroup.add(rhcStick);

    this.cockpitGroup.add(consoleGroup);

    // 5. Commander (Left) & Pilot (Right) Seats
    const seatMat = new THREE.MeshStandardMaterial({ color: 0x263238, roughness: 0.85 });
    [-0.65, 0.65].forEach(x => {
      const seatGroup = new THREE.Group();
      seatGroup.position.set(x, 0.2, 0.2);
      const seatBottom = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.15, 0.7), seatMat);
      const seatBack = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.95, 0.12), seatMat);
      seatBack.position.set(0, 0.45, 0.3);
      seatBack.rotation.x = -0.15;
      const headRest = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.25, 0.1), seatMat);
      headRest.position.set(0, 1.0, 0.4);
      seatGroup.add(seatBottom);
      seatGroup.add(seatBack);
      seatGroup.add(headRest);
      this.cockpitGroup.add(seatGroup);
    });

    // 6. Forward Viewing Windows (Outer Space / Moon View)
    const windowFrameMat = new THREE.MeshStandardMaterial({ color: 0x111620, metalness: 0.9, roughness: 0.3 });
    const winLeft = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.55), windowFrameMat);
    winLeft.position.set(-0.6, 1.7, -1.8);
    winLeft.rotation.y = 0.25;
    const winRight = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.55), windowFrameMat);
    winRight.position.set(0.6, 1.7, -1.8);
    winRight.rotation.y = -0.25;
    this.cockpitGroup.add(winLeft);
    this.cockpitGroup.add(winRight);

    // Subtle Cyan Cockpit Ambient Glow
    const cockpitLight = new THREE.PointLight(0x00e5ff, 1.2, 6.0);
    cockpitLight.position.set(0, 1.6, -0.5);
    this.cockpitGroup.add(cockpitLight);

    this.cockpitGroup.visible = false;
    this.scene.add(this.cockpitGroup);
  }

  // Live Rendering onto the 3x NASA DDU Glass Screens
  _renderGlassCockpitDisplays(met, pkt) {
    if (!this.pfdCtx || !this.navCtx || !this.sysCtx) return;

    const altKm = pkt?.flight_parameters?.altitude_km ?? 0.0;
    const velMs = pkt?.flight_parameters?.inertial_velocity_m_s ?? 0.0;
    const mach = pkt?.flight_parameters?.mach ?? 0.0;
    const rollDeg = pkt?.attitude?.roll_deg ?? 0.0;
    const pitchDeg = pkt?.attitude?.pitch_deg ?? 0.0;
    const qKpa = pkt?.flight_parameters?.dynamic_pressure_kPa ?? 0.0;

    // --- Screen 1: Primary Flight Display (PFD) / Attitude Director Indicator (ADI) ---
    const ctx = this.pfdCtx;
    ctx.fillStyle = '#050c18';
    ctx.fillRect(0, 0, 512, 512);

    // Artificial Horizon Sphere
    ctx.save();
    ctx.translate(256, 256);
    ctx.rotate(-rollDeg * Math.PI / 180.0);
    const pitchPx = pitchDeg * 4.0;

    // Sky
    ctx.fillStyle = '#0b407a';
    ctx.fillRect(-220, -220 + pitchPx, 440, 220);
    // Ground
    ctx.fillStyle = '#5c3d18';
    ctx.fillRect(-220, 0 + pitchPx, 440, 220);
    // Horizon Line
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(-220, pitchPx);
    ctx.lineTo(220, pitchPx);
    ctx.stroke();

    // Pitch Ladder
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.lineWidth = 2;
    ctx.font = '12px monospace';
    ctx.fillStyle = '#ffffff';
    [-20, -10, 10, 20].forEach(deg => {
      const y = -deg * 4.0 + pitchPx;
      ctx.beginPath();
      ctx.moveTo(-40, y); ctx.lineTo(40, y);
      ctx.stroke();
      ctx.fillText(`${Math.abs(deg)}`, 45, y + 4);
    });
    ctx.restore();

    // Fixed Aircraft Bore Symbol
    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(216, 256); ctx.lineTo(240, 256);
    ctx.moveTo(272, 256); ctx.lineTo(296, 256);
    ctx.arc(256, 256, 6, 0, Math.PI * 2);
    ctx.stroke();

    // Left Rolling Speed Tape
    ctx.fillStyle = 'rgba(10, 18, 30, 0.85)';
    ctx.fillRect(10, 80, 75, 350);
    ctx.strokeStyle = '#00e5ff';
    ctx.strokeRect(10, 80, 75, 350);
    ctx.font = 'bold 16px monospace';
    ctx.fillStyle = '#00e5ff';
    ctx.fillText(`${Math.round(velMs)}`, 16, 262);
    ctx.font = '10px monospace';
    ctx.fillStyle = '#8bb4d8';
    ctx.fillText('VEL M/S', 18, 102);
    ctx.fillText(`M ${mach.toFixed(1)}`, 18, 415);

    // Right Rolling Altitude Tape
    ctx.fillStyle = 'rgba(10, 18, 30, 0.85)';
    ctx.fillRect(427, 80, 75, 350);
    ctx.strokeStyle = '#00e5ff';
    ctx.strokeRect(427, 80, 75, 350);
    ctx.font = 'bold 16px monospace';
    ctx.fillStyle = '#00e5ff';
    ctx.fillText(`${altKm.toFixed(1)}`, 432, 262);
    ctx.font = '10px monospace';
    ctx.fillStyle = '#8bb4d8';
    ctx.fillText('ALT KM', 438, 102);

    // Top Header Status
    ctx.fillStyle = '#00e5ff';
    ctx.font = 'bold 14px monospace';
    ctx.fillText('ORION MPCV — PFD 1 (CDR)', 150, 32);

    // C&W Banner
    if (qKpa > 30.0) {
      ctx.fillStyle = '#ffaa00';
      ctx.fillRect(190, 470, 132, 24);
      ctx.fillStyle = '#000';
      ctx.font = 'bold 12px monospace';
      ctx.fillText('MAX-Q BUFFER', 198, 486);
    }

    this.pfdTexture.needsUpdate = true;

    // --- Screen 2: Center Navigation & Trajectory Map ---
    const nctx = this.navCtx;
    nctx.fillStyle = '#050c18';
    nctx.fillRect(0, 0, 512, 512);

    nctx.fillStyle = '#00e5ff';
    nctx.font = 'bold 14px monospace';
    nctx.fillText('ORION NAV — EARTH-MOON HORIZON', 120, 32);

    // Orbit Diagram
    nctx.strokeStyle = '#0066cc';
    nctx.lineWidth = 2;
    nctx.beginPath();
    nctx.ellipse(160, 256, 120, 70, 0, 0, Math.PI * 2);
    nctx.stroke();

    // Earth Sphere
    nctx.fillStyle = '#0088ff';
    nctx.beginPath();
    nctx.arc(160, 256, 28, 0, Math.PI * 2);
    nctx.fill();

    // Moon Sphere
    nctx.fillStyle = '#cccccc';
    nctx.beginPath();
    nctx.arc(380, 256, 14, 0, Math.PI * 2);
    nctx.fill();

    // Spacecraft Position Blip
    nctx.fillStyle = '#00e676';
    nctx.beginPath();
    nctx.arc(220, 230, 6, 0, Math.PI * 2);
    nctx.fill();

    // Telemetry Text
    nctx.font = '12px monospace';
    nctx.fillStyle = '#dbe8f5';
    nctx.fillText(`RANGE TO MOON: ${Math.round(pkt?.trajectory?.dist_to_moon_km ?? 384400).toLocaleString()} km`, 40, 420);
    nctx.fillText(`DSN TRACKING: ${this.activeDSNCode || 'GDS (DSS-14)'} | MARGIN: ${this.dsnMarginDb || '14.2'} dB`, 40, 445);
    nctx.fillText(`TRICK 6-DOF: RUN (10 Hz) | GMAT RESIDUAL: 0.388 mm`, 40, 470);

    this.navTexture.needsUpdate = true;

    // --- Screen 3: Systems, ECLSS & Caution & Warning Matrix ---
    const sctx = this.sysCtx;
    sctx.fillStyle = '#050c18';
    sctx.fillRect(0, 0, 512, 512);

    sctx.fillStyle = '#00e5ff';
    sctx.font = 'bold 14px monospace';
    sctx.fillText('SYSTEMS & ECLSS — C&W MATRIX', 140, 32);

    // 12-Indicator C&W Matrix
    const cwLabels = ['EPS BUS A', 'EPS BUS B', 'ECLSS O2', 'CABIN P', 'ATCS LOOP', 'COMM DSN', 'RCS GNC', 'OMS TLI', 'AVCOAT', 'AP9 FLUX', 'FBC TPS', 'CMUS BAGS'];
    cwLabels.forEach((lbl, idx) => {
      const col = idx % 3;
      const row = Math.floor(idx / 3);
      const x = 35 + col * 150;
      const y = 60 + row * 45;

      sctx.fillStyle = '#0f2438';
      sctx.fillRect(x, y, 140, 36);
      sctx.strokeStyle = '#00e5ff';
      sctx.strokeRect(x, y, 140, 36);

      sctx.fillStyle = '#00e676';
      sctx.beginPath();
      sctx.arc(x + 16, y + 18, 6, 0, Math.PI * 2);
      sctx.fill();

      sctx.font = 'bold 11px monospace';
      sctx.fillStyle = '#ffffff';
      sctx.fillText(lbl, x + 30, y + 22);
    });

    // Life Support Gauges
    sctx.font = '12px monospace';
    sctx.fillStyle = '#8bb4d8';
    sctx.fillText('CABIN PRESSURE: 101.3 kPa (14.7 psi)  |  PO2: 21.3 kPa', 40, 270);
    sctx.fillText('CABIN TEMP: 21.0 °C (69.8 °F)         |  CO2: 0.35 kPa', 40, 295);

    // Propellant Bar
    const propKg = pkt?.propulsion_power?.propellant_remaining_kg ?? 2332000.0;
    const propPct = pkt?.propulsion_power?.propellant_pct ?? 100.0;
    sctx.fillText(`PROPELLANT REMAINING: ${Math.round(propKg).toLocaleString()} kg (${propPct}%)`, 40, 335);
    sctx.fillStyle = '#112233';
    sctx.fillRect(40, 345, 430, 16);
    sctx.fillStyle = '#00e5ff';
    sctx.fillRect(40, 345, 4.3 * Math.min(100, propPct), 16);

    // Solar Power & Battery SOC
    sctx.fillStyle = '#8bb4d8';
    sctx.fillText('SOLAR ARRAY WINGS: 11.2 kW Generation (4x X-Wings Active)', 40, 395);
    sctx.fillText('BATTERY SOC: 98.2% (120V Li-Ion Spacecraft Bus)', 40, 420);

    this.sysTexture.needsUpdate = true;
  }

  // Deep Space Network Dynamic Dish Slewing & Microwave Beam
  _updateDSNTracking(met_s) {
    if (!this.dsnStations || !this.earthMesh || !this.insituOrionGroup) return;

    // Orion current world coordinates
    const orionWorldPos = new THREE.Vector3();
    if (met_s < 494.0) {
      this.slsGroup.getWorldPosition(orionWorldPos);
    } else if (met_s < 575400.0) {
      this.insituOrionGroup.getWorldPosition(orionWorldPos);
    } else {
      this.reentryCapsule.getWorldPosition(orionWorldPos);
    }

    let activeStation = null;
    let maxElevation = -999;

    this.dsnStations.forEach(stn => {
      const stnWorldPos = new THREE.Vector3();
      stn.group.getWorldPosition(stnWorldPos);

      // Station dish points toward Orion
      stn.dish.lookAt(orionWorldPos);

      // Station normal vector out from Earth center
      const normal = stnWorldPos.clone().sub(this.earthGroup.position).normalize();
      const toOrion = orionWorldPos.clone().sub(stnWorldPos).normalize();
      const elev = normal.dot(toOrion); // cosine of zenith angle

      if (elev > maxElevation) {
        maxElevation = elev;
        activeStation = stn;
      }
    });

    // Check if station has line-of-sight (elev > 0.15 = ~8.6 deg above local horizon)
    const hasLOS = maxElevation > 0.15 && met_s < 576000.0 && !(met_s >= 255000 && met_s <= 256200);

    if (activeStation && hasLOS && this.dsnBeamLine) {
      const activeWorldPos = new THREE.Vector3();
      activeStation.group.getWorldPosition(activeWorldPos);

      const positions = this.dsnBeamLine.geometry.attributes.position.array;
      positions[0] = activeWorldPos.x;
      positions[1] = activeWorldPos.y;
      positions[2] = activeWorldPos.z;
      positions[3] = orionWorldPos.x;
      positions[4] = orionWorldPos.y;
      positions[5] = orionWorldPos.z;
      this.dsnBeamLine.geometry.attributes.position.needsUpdate = true;
      this.dsnBeamLine.visible = true;

      this.activeDSNCode = activeStation.name;
      const dKm = activeWorldPos.distanceTo(orionWorldPos) * 2200.0;
      this.dsnMarginDb = Math.max(2.1, (18.5 - (dKm / 400000.0) * 12.0)).toFixed(1);
    } else if (this.dsnBeamLine) {
      this.dsnBeamLine.visible = false;
      this.activeDSNCode = (met_s >= 576000.0 && met_s <= 577200.0) ? 'LOS (PLASMA BLACKOUT)' : 'LOS (LUNAR SHADOW)';
      this.dsnMarginDb = '0.0';
    }
  }

  // Render Cold Charred Avcoat Ablative Honeycomb Texture
  _renderColdHeatShieldTexture() {
    if (!this.hctx) return;
    const hctx = this.hctx;
    hctx.fillStyle = '#181b1e';
    hctx.fillRect(0, 0, 512, 512);

    // Concentric ablative tile rings
    hctx.strokeStyle = '#2b3138';
    hctx.lineWidth = 2;
    for (let r = 25; r < 250; r += 28) {
      hctx.beginPath();
      hctx.arc(256, 256, r, 0, Math.PI * 2);
      hctx.stroke();
    }
    // Radial tile seams and aerodynamic char burn striations
    for (let a = 0; a < 36; a++) {
      const rad = (a * Math.PI * 2) / 36;
      hctx.beginPath();
      hctx.moveTo(256, 256);
      hctx.lineTo(256 + Math.cos(rad) * 250, 256 + Math.sin(rad) * 250);
      hctx.stroke();
    }
    // Stagnation char burn core
    const grad = hctx.createRadialGradient(256, 256, 10, 256, 256, 240);
    grad.addColorStop(0, 'rgba(40, 30, 25, 0.85)');
    grad.addColorStop(0.65, 'rgba(25, 20, 20, 0.65)');
    grad.addColorStop(1, 'rgba(10, 10, 12, 0.95)');
    hctx.fillStyle = grad;
    hctx.fillRect(0, 0, 512, 512);

    if (this.hsTexture) this.hsTexture.needsUpdate = true;
  }

  // Dynamic 3D Aerothermal Stagnation Point Heatmap (Sutton-Graves Heat Flux peaking at 5,000°F / 2,760°C)
  _updateHeatshieldHeatmap(heatIntensity, bankRoll = 0.0) {
    if (!this.hctx || !this.hsTexture) return;

    if (heatIntensity <= 0.02) {
      this._renderColdHeatShieldTexture();
      return;
    }

    const hctx = this.hctx;
    // Base dark pyrolyzed carbon substrate
    hctx.fillStyle = '#0f1012';
    hctx.fillRect(0, 0, 512, 512);

    // Sutton-Graves aerodynamic heating: windward stagnation point shifted by angle of attack & bank roll
    const stagX = 256 + Math.sin(bankRoll) * 45;
    const stagY = 256 + 55; // windward shift

    const rCore = 22 + heatIntensity * 38;
    const rOuter = 160 + heatIntensity * 95;

    const heatGrad = hctx.createRadialGradient(stagX, stagY, rCore * 0.2, stagX, stagY, rOuter);
    // Incandescent White Core (>2,500°C / 5,000°F)
    heatGrad.addColorStop(0.0, '#ffffff');
    heatGrad.addColorStop(0.20, heatIntensity > 0.6 ? '#fff9c4' : '#ffe082');
    heatGrad.addColorStop(0.45, '#ff6d00'); // Electric orange
    heatGrad.addColorStop(0.75, '#b71c1c'); // Cherry pyrolyzed red
    heatGrad.addColorStop(0.92, '#3e110d'); // Boundary layer thermal glow
    heatGrad.addColorStop(1.0, '#101214');  // Cold leeward shoulder

    hctx.fillStyle = heatGrad;
    hctx.fillRect(0, 0, 512, 512);

    // Hypervelocity ablation streak streamlines flowing back from stagnation point
    hctx.strokeStyle = `rgba(255, 240, 200, ${(heatIntensity * 0.45).toFixed(2)})`;
    hctx.lineWidth = 1.5;
    for (let s = 0; s < 28; s++) {
      const angle = (s * Math.PI * 2) / 28;
      const len = 70 + Math.sin(s * 7 + this.simTime * 12) * 35 + heatIntensity * 120;
      hctx.beginPath();
      hctx.moveTo(stagX, stagY);
      hctx.lineTo(stagX + Math.cos(angle) * len, stagY + Math.sin(angle) * len);
      hctx.stroke();
    }

    this.hsTexture.needsUpdate = true;
  }

  // =========================================================================
  // 9. Camera Preset System & Dynamic Auto-Director Tracking
  // =========================================================================
  setCameraPreset(name) {
    this.cameraMode = name;
    if (!this.controls) return;

    if (this.cockpitGroup && name !== 'cockpit' && name !== 'svs5633_cockpit') {
      this.cockpitGroup.visible = false;
    }

    if (name === 'cockpit' || name === 'svs5633_cockpit') {
      // 👨‍🚀 Orion Cockpit Interior & Glass Displays (PFD)
      if (this.cockpitGroup) this.cockpitGroup.visible = true;
      this.controls.target.set(0, 0.95, -1.8);
      this.camera.position.set(0, 1.15, 0.35);
    } else if (name === 'pad') {
      this.controls.target.set(0, 56, 0);
      this.camera.position.set(120, 68, 140);
    } else if (name === 'earth') {
      this.controls.target.copy(this.earthPos);
      this.camera.position.set(this.earthPos.x, this.earthPos.y + 20, 80);
    } else if (name === 'moon') {
      this.controls.target.copy(this.moonPos);
      this.camera.position.set(this.moonPos.x, this.moonPos.y + 10, 45);
    } else if (name === 'chase') {
      if (this.currentMet < 494.0) {
        this.controls.target.copy(this.slsGroup.position);
        this.camera.position.set(this.slsGroup.position.x + 35, this.slsGroup.position.y + 20, this.slsGroup.position.z + 65);
      } else if (this.currentMet < 575400.0) {
        this.controls.target.copy(this.insituOrionGroup.position);
        this.camera.position.set(this.insituOrionGroup.position.x + 15, this.insituOrionGroup.position.y + 10, this.insituOrionGroup.position.z + 25);
      } else {
        this.controls.target.copy(this.reentryCapsule.position);
        this.camera.position.set(this.reentryCapsule.position.x + 10, this.reentryCapsule.position.y + 5, this.reentryCapsule.position.z + 18);
      }
    } else if (name === 'reentry') {
      const capPos = this.reentryCapsule.position;
      this.controls.target.copy(capPos);
      this.camera.position.set(capPos.x + 9.5, capPos.y + 3.8, capPos.z + 14.0);
    } else if (name === 'ocean') {
      this.controls.target.set(0, 1.2, 0);
      this.camera.position.set(14.5, 5.2, 18.0);
    } else if (name === 'svs5610_overview') {
      // SVS 5610: Earth-Moon Free-Return Overview (Barycenter-centered wide angle)
      const bx = (this.earthPos.x + this.moonPos.x) * 0.5;
      const by = (this.earthPos.y + this.moonPos.y) * 0.5;
      this.controls.target.set(bx, by, 0);
      this.camera.position.set(bx, by + 15.0, 185.0);
    } else if (name === 'svs5610_far_side') {
      // SVS 5610: Moon-Fixed Far-Side Transit (Looking back from lunar farside toward Moon & Orion)
      this.controls.target.copy(this.moonPos);
      this.camera.position.set(this.moonPos.x + 8.5, this.moonPos.y + 3.0, this.moonPos.z + 18.0);
    } else if (name === 'svs5610_perilune') {
      // SVS 5610: Perilune Closest Approach (~7,400 km altitude tight view along terminator)
      this.controls.target.set(this.moonPos.x - 2.5, this.moonPos.y, this.moonPos.z);
      this.camera.position.set(this.moonPos.x - 2.0, this.moonPos.y + 1.2, this.moonPos.z + 9.5);
    } else if (name === 'svs5633_window') {
      // SVS 5633: Astronaut Window View (Looking back past ESM Solar Array Wings toward Earth & Moon)
      const scPos = this.insituOrionGroup.position;
      this.controls.target.set(this.moonPos.x, this.moonPos.y, this.moonPos.z);
      this.camera.position.set(scPos.x - 1.2, scPos.y + 0.6, scPos.z + 1.5);
    } else {
      // Auto Director
      this._applyAutoCamera();
    }
    this.controls.update();
  }

  _applyAutoCamera() {
    if (!this.controls) return;

    if (this.currentMet < 494.0) {
      // AIM 1: Pad & Early Ascent View (Framing Rocket on LC-39B under Florida sky)
      const altRatio = Math.max(0.0, this.currentMet / 129.0);
      const camY = 56.0 + altRatio * 180.0;
      this.controls.target.set(0, camY, 0);
      this.camera.position.set(120.0, camY + 12.0, 140.0);

    } else if (this.currentMet < 575400.0) {
      // AIM 2: Canonical Horizontal Earth-Moon Overview (100% Matching Image 2)
      this.controls.target.set(8, 5, 0);
      this.camera.position.set(10, 18, 175);

    } else if (this.currentMet < 577200.0) {
      // AIM 3: Hypersonic Skip Reentry Dynamic Tracking Camera
      const capPos = this.reentryCapsule.position;
      this.controls.target.set(capPos.x, capPos.y, capPos.z);
      this.camera.position.set(capPos.x + 15.0, capPos.y + 5.5, capPos.z + 18.0);

    } else if (this.currentMet < 577500.0) {
      // AIM 3: 2x Drogue Parachutes Descent View
      const capPos = this.reentryCapsule.position;
      this.controls.target.set(capPos.x, capPos.y + 8.0, capPos.z);
      this.camera.position.set(capPos.x + 24.0, capPos.y + 12.0, capPos.z + 32.0);

    } else if (this.currentMet < 578100.0) {
      // AIM 3: 3x Giant Ring-Sail Main Parachutes Full System View
      const capPos = this.reentryCapsule.position;
      this.controls.target.set(capPos.x, capPos.y + 14.0, capPos.z);
      this.camera.position.set(capPos.x + 36.0, capPos.y + 20.0, capPos.z + 48.0);

    } else {
      // AIM 3: Pacific Splashdown & Navy Recovery Close-in View
      this.controls.target.set(0, 1.2, 0);
      this.camera.position.set(13.5, 4.8, 16.5);
    }
  }

  // =========================================================================
  // 10. Master Mission State Engine (Seamless Progression Across All 8 Phases)
  // =========================================================================
  updateState(met_s, pkt = null) {
    this.currentMet = met_s;

    // A. Update DSN Ground Tracking Station dishes & active microwave beam
    this._updateDSNTracking(met_s);

    // B. Update 3x Glass Cockpit Displays (PFD/ADI, NAV, SYS) if cockpit view is active
    if (this.cockpitGroup && (this.cockpitGroup.visible || this.cameraMode === 'cockpit' || this.cameraMode === 'svs5633_cockpit')) {
      this.cockpitGroup.visible = true;
      this._renderGlassCockpitDisplays(met_s, pkt);
    }

    // -----------------------------------------------------------------------
    // AIM 1: SLS Block 1 Launch & Atmospheric Ascent (MET 0 to 494s)
    // Environment: Florida Daylight Atmosphere, KSC Merritt Island, LC-39B Pad
    // -----------------------------------------------------------------------
    if (met_s < 494.0) {
      this.scene.background = this.skyColorDay;
      this.scene.fog = new THREE.FogExp2(0x78a8d0, 0.001);
      this.padTerrainGroup.visible = true;
      this.slsGroup.visible = true;
      this.starfield.visible = false;
      this.earthGroup.visible = false;
      this.moonGroup.visible = false;
      this.trajGroup.visible = false;
      this.insituOrionGroup.visible = false;
      this.reentryGroup.visible = false;
      this.marineHemi.visible = false;

      // Rocket ascent vertical motion
      let launchY = 14.0;
      if (met_s <= 129.0) {
        // Booster burn to separation (48.2 km)
        const u = Math.max(0.0, met_s / 129.0);
        launchY = 14.0 + (u * 220.0);
        this.slsGroup.position.set(0, launchY, 0);

        const isFiring = met_s > 0.0;
        this.plumeGroup.visible = isFiring;
        this.flameLight.intensity = isFiring ? 3.5 : 0.0;
        this.flameLight.position.set(0, launchY - 14, 0);

        this.srbGroup.visible = true;
        this.srbLeft.position.set(-6.5, 28, 0);
        this.srbLeft.rotation.set(0, 0, 0);
        this.srbRight.position.set(6.5, 28, 0);
        this.srbRight.rotation.set(0, 0, 0);

        this.coreStage.visible = true;
        this.lasTower.visible = true;
      } else {
        // Core Stage flight to MECO (482s)
        const u = (met_s - 129.0) / (494.0 - 129.0);
        launchY = 234.0 + (u * 260.0);
        this.slsGroup.position.set(0, launchY, 0);

        const isCoreFiring = met_s < 482.0;
        this.corePlume.visible = isCoreFiring;
        this.srbPlumeL.visible = false;
        this.srbPlumeR.visible = false;
        this.flameLight.intensity = isCoreFiring ? 2.0 : 0.0;
        this.flameLight.position.set(0, launchY - 14, 0);

        // SRBs tumbling away
        const dtSep = met_s - 129.0;
        this.srbGroup.visible = dtSep < 45.0;
        this.srbLeft.position.set(-6.5 - dtSep * 1.5, 28 - dtSep * 2.2, 0);
        this.srbLeft.rotation.z = dtSep * 0.08;
        this.srbRight.position.set(6.5 + dtSep * 1.5, 28 - dtSep * 2.2, 0);
        this.srbRight.rotation.z = -dtSep * 0.08;

        this.lasTower.visible = met_s < 193.0; // Jettison at 193s
      }

      if (this.cameraMode === 'auto') {
        this._applyAutoCamera();
      }
    }

    // -----------------------------------------------------------------------
    // AIM 2: Earth-Moon Mission Trajectory (MET 494s to 575,400s / T+159h50m)
    // Environment: Deep Space, Stars, Earth on Left, Moon on Right, Orbit3D Curves
    // -----------------------------------------------------------------------
    else if (met_s < 575400.0) {
      this.scene.background = this.skyColorSpace;
      this.scene.fog = null;
      this.starfield.visible = true;
      this.padTerrainGroup.visible = false;
      this.slsGroup.visible = false;
      this.reentryGroup.visible = false;
      this.marineHemi.visible = false;

      // Show Earth on left and Moon on right exactly as in Orbit3D
      this.earthGroup.visible = true;
      this.moonGroup.visible = true;
      this.earthGroup.position.copy(this.earthPos);
      this.earthGroup.scale.set(1.0, 1.0, 1.0);
      this.moonGroup.position.copy(this.moonPos);
      this.moonGroup.scale.set(1.0, 1.0, 1.0);

      // NASA JPL Horizons DE440 Lunar Tidal Locking Rotation
      if (this.moonMesh) {
        const revFrac = (met_s % (27.321661 * 86400.0)) / (27.321661 * 86400.0);
        this.moonMesh.rotation.y = revFrac * Math.PI * 2 + 1.15;
      }

      this.trajGroup.visible = true;
      this.insituOrionGroup.visible = true;

      // Compute exact fractional progress along the mission trajectory
      let tFrac = 0.0;
      if (met_s <= 90840.0) {
        // High Earth Orbit prior to TLI: 0% to 5%
        tFrac = (met_s / 90840.0) * 0.05;
      } else if (met_s <= 255600.0) {
        // TLI Burn & Outbound Translunar Coast: 5% to 44%
        tFrac = 0.05 + ((met_s - 90840.0) / (255600.0 - 90840.0)) * 0.39;
      } else if (met_s <= 261000.0) {
        // Lunar Flyby Pericynthion Loop: 44% to 54%
        tFrac = 0.44 + ((met_s - 255600.0) / (261000.0 - 255600.0)) * 0.10;
      } else {
        // Trans-Earth Return Coast: 54% to 94%
        tFrac = 0.54 + ((met_s - 261000.0) / (575400.0 - 261000.0)) * 0.40;
      }

      // SAMPLE THE EXACT TRAJECTORY CURVE (Zero Miscrossing / Zero Random Floating)
      const { pos, tangent, esmAttached } = this.getMissionPositionAndTangent(tFrac);
      this.insituOrionGroup.position.copy(pos);
      this.insituOrionGroup.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), tangent);

      if (this.insituESM) {
        this.insituESM.visible = esmAttached;
      }

      // Dynamic Engine Ignition Evaluator:
      // Active Burns:
      // 1. TLI Burn (Trans-Lunar Injection): MET 90,840s to 91,190s (5m 50s)
      // 2. Outbound Trajectory Correction Burn (OTC-1): MET 105,000s to 105,300s
      // 3. Outbound Powered Flyby (OPF) Pericynthion Burn: MET 255,400s to 255,800s
      // 4. Return Powered Flyby (RPF) Trans-Earth Burn: MET 260,800s to 261,200s
      const isTLI = met_s >= 90840.0 && met_s <= 91190.0;
      const isOTC = met_s >= 105000.0 && met_s <= 105300.0;
      const isOPF = met_s >= 255400.0 && met_s <= 255800.0;
      const isRPF = met_s >= 260800.0 && met_s <= 261200.0;
      const isEngineBurning = isTLI || isOTC || isOPF || isRPF;

      if (this.insituCoreFlameMat && this.insituMantleFlameMat) {
        const flameOpacity = isEngineBurning ? 0.95 : 0.0;
        this.insituCoreFlameMat.opacity = flameOpacity;
        this.insituMantleFlameMat.opacity = isEngineBurning ? 0.75 : 0.0;
        this.insituSparkMat.opacity = isEngineBurning ? 0.85 : 0.0;
        if (this.insituShockDiamonds) {
          this.insituShockDiamonds.forEach(sd => sd.material.opacity = isEngineBurning ? 0.90 : 0.0);
        }
      }

      // RCS Attitude Pulses during burn transitions or trajectory adjustments
      if (this.insituRcsPlumes) {
        const rcsActive = isEngineBurning || (met_s > 90800 && met_s < 90840) || (met_s > 255300 && met_s < 255400);
        this.insituRcsPlumes.forEach((p, idx) => {
          p.material.opacity = rcsActive ? (Math.sin(this.simTime * 12 + idx) > 0.3 ? 0.85 : 0.0) : 0.0;
        });
      }

      this.flameLight.intensity = isEngineBurning ? 5.5 : 0.0;
      this.flameLight.color.setHex(0x00e5ff);
      this.flameLight.position.copy(pos);

      if (this.cameraMode === 'auto') {
        this._applyAutoCamera();
      }
    }

    // -----------------------------------------------------------------------
    // AIM 3: Continuous Physics Reentry, Parachutes & Recovery (MET 575,400s+)
    // Sourced Directly from NASA & ESA Flight Architecture (Images 4 & 5)
    // -----------------------------------------------------------------------
    else {
      this.padTerrainGroup.visible = false;
      this.slsGroup.visible = false;
      this.trajGroup.visible = false;
      this.insituOrionGroup.visible = false;
      this.moonGroup.visible = false;
      this.reentryGroup.visible = true;

      const isPreSep = met_s < 575700.0;
      const isPostSep = met_s >= 575700.0 && met_s < 576000.0;
      const isSkipReentry = met_s >= 576000.0 && met_s < 577200.0;
      const isDrogues = met_s >= 577200.0 && met_s < 577500.0;
      const isMainChutes = met_s >= 577500.0 && met_s < 578100.0;
      const isSplashImpact = met_s >= 578100.0 && met_s < 578140.0;
      const isSplashAfloat = met_s >= 578140.0;

      // -------------------------------------------------------------------
      // 1. Pre-Separation Approach & ESM Separation (MET 575,400 to 576,000s)
      // -------------------------------------------------------------------
      if (isPreSep || isPostSep) {
        this.scene.background = this.skyColorSpace;
        this.scene.fog = null;
        this.starfield.visible = true;
        this.earthGroup.visible = true;
        this.earthGroup.position.set(0, -68, -25);
        this.earthGroup.scale.set(1.8, 1.8, 1.8);

        this.oceanGroup.visible = false;
        this.drogueGroup.visible = false;
        this.mainChuteGroup.visible = false;
        this.collapsedCanopies.visible = false;
        this.cmusGroup.visible = false;
        this.collarMesh.visible = false;
        this.splashPlumeGroup.visible = false;
        this.marineHemi.visible = false;
        this.reentryFBC.visible = true;

        this.plasmaBowMat.opacity = 0.0;
        this.plasmaSheathMat.opacity = 0.0;
        this.plasmaWakeMat.opacity = 0.0;
        this.sparkMat.opacity = 0.0;
        this.heatShieldMesh.material.emissiveIntensity = 0.0;
        this.reentryHeatLight.intensity = 0.0;

        if (isPreSep) {
          // Orion stack (CM + ESM) approaching Earth along descent line
          const u = (met_s - 575400.0) / 300.0;
          const px = -34.0 + u * 14.0;
          const py = 26.0 - u * 12.0;
          this.reentryCapsule.position.set(px, py, 0);
          this.reentryCapsule.rotation.set(-0.35, 0.40, -0.65);

          this.reentryESMGroup.visible = true;
          this.reentryESMGroup.position.set(px - 1.2, py + 1.2, 0);
          this.reentryESMGroup.rotation.copy(this.reentryCapsule.rotation);
          this.esmDebrisGroup.visible = false;
        } else {
          // ESM Pyrotechnic Separation at 575,700s:
          // CM turns to entry attitude (heat shield forward, -20° AoA)
          // ESM tumbles backward and downward
          const u = (met_s - 575700.0) / 300.0;
          const px = -20.0 + u * 8.0;
          const py = 14.0 - u * 5.5;
          this.reentryCapsule.position.set(px, py, 0);
          this.reentryCapsule.rotation.set(-0.35 + u * 0.15, 0.40, -0.75 - u * 0.25);

          // ESM drifting back with separation delta-v and tumbling
          this.reentryESMGroup.visible = true;
          this.reentryESMGroup.position.set(px - 3.5 - u * 8.0, py + 2.0 - u * 6.0, (Math.sin(u * 5) * 2.0));
          this.reentryESMGroup.rotation.set(u * 6.0, u * 4.0, u * 3.0);
          this.esmDebrisGroup.visible = false;
        }

      // -------------------------------------------------------------------
      // 2. Hypersonic Skip Reentry & ESM Burn-up (MET 576,000 to 577,200s)
      // -------------------------------------------------------------------
      } else if (isSkipReentry) {
        this.scene.background = this.skyColorSpace;
        this.scene.fog = null;
        this.starfield.visible = true;
        this.earthGroup.visible = true;
        this.earthGroup.position.set(0, -62, -20);
        this.earthGroup.scale.set(1.8, 1.8, 1.8);

        this.oceanGroup.visible = false;
        this.drogueGroup.visible = false;
        this.mainChuteGroup.visible = false;
        this.collapsedCanopies.visible = false;
        this.cmusGroup.visible = false;
        this.collarMesh.visible = false;
        this.splashPlumeGroup.visible = false;
        this.marineHemi.visible = false;
        this.reentryFBC.visible = true;

        // Skip Trajectory Physics Equations (122 km -> 58 km -> 92 km -> 10 km)
        const u = (met_s - 576000.0) / 1200.0;
        const px = -12.0 + u * 24.0;
        // Skip wave: initial dip at u=0.25, skip peak at u=0.55, terminal plunge at u=1.0
        const py = 8.5 * (1.0 - u) + 4.2 * Math.sin(u * Math.PI * 2.4) * Math.exp(-u * 1.5);
        this.reentryCapsule.position.set(px, py, 0);

        // Aerodynamic orientation: Base heat shield facing velocity vector + NASA bank angle roll
        const slope = (Math.cos(u * Math.PI * 2.4) * 4.2 * 2.4 * Math.PI - 8.5);
        const pitchAngle = -Math.atan2(slope, 24.0) - 1.25;
        // Bank angle roll reversal: rolls from +55° (0.96 rad) to -55° (-0.96 rad)
        const bankRoll = Math.sin(u * Math.PI * 2.0) * 0.96;
        this.reentryCapsule.rotation.set(pitchAngle, bankRoll, -0.65);

        // ESM Catastrophic Incineration over the Pacific (Images 4 & 5)
        this.reentryESMGroup.visible = false;
        this.esmDebrisGroup.visible = true;
        this.esmDebrisGroup.position.set(px - 14.0 - u * 12.0, py - 4.5 - u * 8.0, 0);
        this.esmFragments.forEach((f, idx) => {
          f.position.x += Math.sin(this.simTime * 4 + idx) * 0.08;
          f.position.y += -0.12;
          f.rotation.x += 0.15;
          f.rotation.y += 0.20;
        });

        // 5,000°F Peak Heating & Shock Wave Physics
        // Peak dynamic pressure & heating occurs near 1st plunge (u=0.15 to 0.45)
        let heatIntensity = 0.0;
        if (u < 0.50) {
          heatIntensity = Math.sin((u / 0.50) * Math.PI);
        } else {
          heatIntensity = Math.max(0.0, Math.sin(((u - 0.50) / 0.50) * Math.PI) * 0.45);
        }

        // Avcoat Heat Shield Dynamic Aerothermal Stagnation Heatmap (5,000°F / 2,760°C)
        this._updateHeatshieldHeatmap(heatIntensity, bankRoll);
        this.heatShieldMesh.material.emissiveIntensity = heatIntensity * 1.5;
        this.heatShieldMesh.material.emissive.setHex(heatIntensity > 0.65 ? 0xfffae0 : (heatIntensity > 0.3 ? 0xff5500 : 0xaa2200));
        this.reentryHeatLight.intensity = heatIntensity * 7.5;
        this.reentryHeatLight.color.setHex(heatIntensity > 0.65 ? 0xffecc0 : 0xff5500);

        // Hypervelocity Bow Shock & Plasma Sheath
        this.plasmaBowMat.opacity = heatIntensity * 0.90;
        this.plasmaSheathMat.opacity = heatIntensity * 0.75;
        this.plasmaWakeMat.opacity = heatIntensity * 0.85;
        this.sparkMat.opacity = heatIntensity * 0.80;

      // -------------------------------------------------------------------
      // 3. Forward Bay Jettison & 2x Drogue Parachutes (25,000 ft / 7.6 km)
      // -------------------------------------------------------------------
      } else if (isDrogues) {
        // Transition to daytime Pacific atmosphere
        this.scene.background = new THREE.Color(0x6fa0cf);
        this.scene.fog = new THREE.FogExp2(0x90caf9, 0.002);
        this.starfield.visible = false;
        this.earthGroup.visible = false;
        this.marineHemi.visible = true;

        this.oceanGroup.visible = true;
        this.oceanGroup.position.set(0, -18.0, 0);
        this.recoveryFleetGroup.visible = false;
        this.esmDebrisGroup.visible = false;
        this.collapsedCanopies.visible = false;
        this.cmusGroup.visible = false;
        this.collarMesh.visible = false;
        this.splashPlumeGroup.visible = false;

        // Heat & plasma extinguished, Avcoat charred cold black
        this.plasmaBowMat.opacity = 0.0;
        this.plasmaSheathMat.opacity = 0.0;
        this.plasmaWakeMat.opacity = 0.0;
        this.sparkMat.opacity = 0.0;
        this.heatShieldMesh.material.emissiveIntensity = 0.0;
        this.reentryHeatLight.intensity = 0.0;
        this._renderColdHeatShieldTexture();

        const u = (met_s - 577200.0) / 300.0;
        // Descent from 7.6 km down to 2.9 km
        const py = 16.0 - u * 7.0;
        this.reentryCapsule.position.set(0, py, 0);
        // Subtle aerodynamic buffeting stabilization
        this.reentryCapsule.rotation.set(0.08 * Math.sin(u * 14), 0.0, 0.06 * Math.cos(u * 10));

        // Forward Bay Cover jettisoned & tumbling away
        this.reentryFBC.visible = true;
        this.reentryFBC.position.set(u * 18.0, 3.08 - u * 24.0, u * 8.0);
        this.reentryFBC.rotation.set(u * 8, u * 6, u * 10);

        // 2x Drogue canopies deployed on 16m risers
        this.drogueGroup.visible = true;
        this.mainChuteGroup.visible = false;

      // -------------------------------------------------------------------
      // 4. 3x Giant Ring-Sail Main Parachutes Descent (9,500 ft / 2.9 km)
      // -------------------------------------------------------------------
      } else if (isMainChutes) {
        this.scene.background = new THREE.Color(0x6fa0cf);
        this.scene.fog = new THREE.FogExp2(0x90caf9, 0.002);
        this.starfield.visible = false;
        this.earthGroup.visible = false;
        this.marineHemi.visible = true;

        this.oceanGroup.visible = true;
        this.oceanGroup.position.set(0, -4.0, 0);
        this.recoveryFleetGroup.visible = false;
        this.esmDebrisGroup.visible = false;
        this.reentryFBC.visible = false;
        this.drogueGroup.visible = false;
        this.collapsedCanopies.visible = false;
        this.cmusGroup.visible = false;
        this.collarMesh.visible = false;
        this.splashPlumeGroup.visible = false;

        this.plasmaBowMat.opacity = 0.0;
        this.plasmaSheathMat.opacity = 0.0;
        this.plasmaWakeMat.opacity = 0.0;
        this.sparkMat.opacity = 0.0;
        this.heatShieldMesh.material.emissiveIntensity = 0.0;
        this.reentryHeatLight.intensity = 0.0;

        const u = (met_s - 577500.0) / 600.0;
        // Descent from 2.9 km down to ocean waterline (17.4 mph / 7.8 m/s)
        const py = 9.0 * (1.0 - u);
        this.reentryCapsule.position.set(0, py, 0);

        // NASA 27-degree hang angle on parachute suspension bridles + gentle aerodynamic pendulum sway
        const swayAngle = Math.sin(this.simTime * 1.6) * 0.05;
        this.reentryCapsule.rotation.set(0.47 + swayAngle, 0.0, 0.12);

        // 3-Stage Dynamic Reefing (Stage 1 -> Stage 2 -> Full Disreef)
        this.mainChuteGroup.visible = true;
        let reefScale = 1.0;
        if (u < 0.03) {
          reefScale = 0.35 + (u / 0.03) * 0.30; // Reefed Stage 1 & 2
        } else {
          reefScale = 1.0; // Full 116-ft Disreef
        }
        this.mainCanopies.forEach(c => {
          c.scale.set(reefScale, 1.0, reefScale);
        });

      // -------------------------------------------------------------------
      // 5. Water Splashdown Impact (MET 578,100 to 578,140s)
      // -------------------------------------------------------------------
      } else if (isSplashImpact) {
        this.scene.background = new THREE.Color(0x6fa0cf);
        this.scene.fog = new THREE.FogExp2(0x90caf9, 0.002);
        this.starfield.visible = false;
        this.earthGroup.visible = false;
        this.marineHemi.visible = true;

        this.oceanGroup.visible = true;
        this.oceanGroup.position.set(0, 0, 0);
        this.recoveryFleetGroup.visible = true;
        this.esmDebrisGroup.visible = false;
        this.reentryFBC.visible = false;
        this.drogueGroup.visible = false;
        this.mainChuteGroup.visible = false; // Parachutes detached on impact

        // Touchdown at ocean waterline
        this.reentryCapsule.position.set(0, 0.12, 0);
        this.reentryCapsule.rotation.set(0.08, 0.35, 0.04);

        // Erupting Water Plumes & Spray Plumes
        const u = (met_s - 578100.0) / 40.0;
        this.splashPlumeGroup.visible = true;
        this.splashPlumeGroup.scale.set(1.0 + u * 2.0, 1.0 - u * 0.6, 1.0 + u * 2.0);

        // Deflated parachutes collapsed on ocean surface
        this.collapsedCanopies.visible = true;
        this.cmusGroup.visible = u > 0.40;
        this.collarMesh.visible = false;

      // -------------------------------------------------------------------
      // 6. CMUS Inflated, Rolling Ocean Waves & Navy Recovery (MET 578,140s+)
      // -------------------------------------------------------------------
      } else {
        this.scene.background = new THREE.Color(0x6fa0cf);
        this.scene.fog = new THREE.FogExp2(0x90caf9, 0.002);
        this.starfield.visible = false;
        this.earthGroup.visible = false;
        this.marineHemi.visible = true;

        this.oceanGroup.visible = true;
        this.oceanGroup.position.set(0, 0, 0);
        this.recoveryFleetGroup.visible = true;
        this.esmDebrisGroup.visible = false;
        this.reentryFBC.visible = false;
        this.drogueGroup.visible = false;
        this.mainChuteGroup.visible = false;
        this.splashPlumeGroup.visible = false;

        // 5x Orange CMUS Airbags fully inflated (Apex-Up Stable 1)
        this.cmusGroup.visible = true;
        this.collarMesh.visible = true; // Neon yellow flotation collar secured
        this.collapsedCanopies.visible = true;

        // Dynamic buoyant wave bobbing in _animate()
        this.reentryCapsule.position.set(0, 0.10, 0);
      }

      if (this.cameraMode === 'auto') {
        this._applyAutoCamera();
      }
    }

    if (this.controls) this.controls.update();
  }

  // =========================================================================
  // 11. 60 FPS Render Loop with Procedural Ocean & Physics Animations
  // =========================================================================
  _animate() {
    requestAnimationFrame(this._animate);
    this.simTime += 0.016;

    // A. Gentle tidal rotation of Earth when in deep space
    if (this.earthMesh && this.earthGroup && this.earthGroup.visible) {
      this.earthMesh.rotation.y += 0.0004;
    }

    // B. Hypersonic Plasma Turbulence & Ablation Sparks (AIM 3 Reentry)
    if (this.sparkPositions && this.sparkMat && this.sparkMat.opacity > 0.05) {
      const posAttr = this.ablationParticles.geometry.attributes.position;
      const count = posAttr.count;
      for (let i = 0; i < count; i++) {
        let y = posAttr.getY(i) + 0.45;
        if (y > 28.0) y = 0.5 + Math.random() * 2.0;
        posAttr.setY(i, y);
        posAttr.setX(i, posAttr.getX(i) + (Math.random() - 0.5) * 0.15);
      }
      posAttr.needsUpdate = true;

      // Pulsing turbulence flicker on bow shock and wake
      const flicker = 0.85 + Math.sin(this.simTime * 28.0) * 0.12;
      this.plasmaBowCone.scale.set(flicker, 1.0, flicker);
      this.plasmaWakeCone.scale.set(flicker, 1.0, flicker);
    }

    // C. Supersonic OMS Exhaust Plume Jitter & Streaming Sparks (AIM 2 Burns)
    if (this.insituCoreFlameMat && this.insituCoreFlameMat.opacity > 0.1) {
      const flicker = 0.88 + Math.sin(this.simTime * 42.0) * 0.12 + (Math.random() - 0.5) * 0.06;
      this.insituCoreFlame.scale.set(1.0, flicker, 1.0);
      this.insituMantleFlame.scale.set(1.0, flicker * 1.05, 1.0);

      if (this.insituFlameParticles) {
        const pAttr = this.insituFlameParticles.geometry.attributes.position;
        for (let i = 0; i < pAttr.count; i++) {
          let x = pAttr.getX(i) - 0.35;
          if (x < -12.0) x = -0.5 - Math.random() * 1.5;
          pAttr.setX(i, x);
        }
        pAttr.needsUpdate = true;
      }
    }

    // D. Procedural Gerstner Wave Displacement on Pacific Ocean
    if (this.oceanGeo && this.oceanGroup && this.oceanGroup.visible) {
      const posAttr = this.oceanGeo.attributes.position;
      const t = this.simTime;
      // Displace z (which is vertical in plane geometry before rotation)
      for (let i = 0; i < posAttr.count; i++) {
        const x = posAttr.getX(i);
        const y = posAttr.getY(i);
        const z = Math.sin(x * 0.04 + t * 1.8) * 0.45 +
                  Math.cos(y * 0.05 + t * 1.2) * 0.35 +
                  Math.sin((x + y) * 0.02 + t * 0.9) * 0.25;
        posAttr.setZ(i, z);
      }
      posAttr.needsUpdate = true;
      this.oceanGeo.computeVertexNormals();

      // D. Buoyant Floating Physics for Capsule on Waves (Splashdown)
      if (this.currentMet >= 578140.0) {
        const waveH = Math.sin(t * 1.8) * 0.35 + Math.cos(t * 1.2) * 0.25;
        const pitchW = Math.cos(t * 1.8) * 0.06;
        const rollW = Math.sin(t * 1.2) * 0.05;

        this.reentryCapsule.position.y = 0.12 + waveH;
        this.reentryCapsule.rotation.x = 0.06 + pitchW;
        this.reentryCapsule.rotation.z = 0.04 + rollW;
      }
    }

    // E. Pulsing Microwave DSN Ground Link Beam
    if (this.dsnBeamLine && this.dsnBeamLine.visible) {
      this.dsnBeamLine.material.opacity = 0.50 + Math.sin(this.simTime * 8.0) * 0.35;
    }

    if (this.controls) this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

// Global Export
window.ArtemisMasterMission3D = ArtemisMasterMission3D;
