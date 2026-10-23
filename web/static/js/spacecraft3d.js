/**
 * NASA Orion MPCV Digital Twin — High-Fidelity 3D Spacecraft & Atmospheric Reentry / Recovery Simulator
 * Sourced from NASA Artemis II Reference Documentation & Operational Flight Guides
 * Features:
 *   - Dimensionally accurate Crew Module (CM): 5.029m base dia, 3.35m height, 32.5 deg half-angle
 *   - Red NASA worm logo, American flag, white thermal protection blanket, charcoal backshell tiles
 *   - Authentic Avcoat ablative heat shield base with spherical contour
 *   - European Service Module (ESM) with 4 canted photovoltaic solar wings (jettisoned before entry)
 *   - Hypersonic Plasma Bow Shock (25,000 MPH / Mach 32.4) & 5,000°F fiery wake streamers
 *   - Curved Earth limb and atmospheric glow layer
 *   - 2 Drogue Parachutes (high-altitude stabilization)
 *   - 3 Main Parachutes with authentic alternating ORANGE & WHITE ring-sail gore striping & suspension risers
 *   - Pacific Ocean Splashdown with 5 inflated orange CMUS (Crew Module Uprighting System) balloons
 *   - Flotation collar, Navy Recovery RHIB, and US Navy Amphibious Ship (USS Portland) well-deck operations
 */

class OrionSpacecraft3D {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.width = this.canvas.clientWidth || 340;
    this.height = this.canvas.clientHeight || 280;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(40, this.width / this.height, 0.1, 500);
    this.camera.position.set(13.5, 7.5, 17.0);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxDistance = 150;
      this.controls.minDistance = 4;
    }

    this.spacecraftGroup = new THREE.Group();
    this.esmGroup = new THREE.Group();
    this.solarWings = [];
    this.rcsThrusters = [];
    this.currentPhase = 'entry_interface';
    this.simTime = 0.0;

    this._initLighting();
    this._buildEarthLimb();
    this._buildCrewModule();
    this._buildHeatShield();
    this._buildServiceModule();
    this._buildSolarArrays();
    this._buildRCSThrusters();
    this._buildReentryFeatures();

    this.spacecraftGroup.add(this.esmGroup);
    this.spacecraftGroup.scale.set(0.68, 0.68, 0.68);
    this.spacecraftGroup.rotation.set(0.35, -0.65, 0.35);
    this.scene.add(this.spacecraftGroup);

    window.addEventListener('resize', () => this._onWindowResize());
    this._animate();
  }

  _initLighting() {
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.60);
    this.scene.add(this.ambientLight);

    // Primary Sun Light
    this.sunLight = new THREE.DirectionalLight(0xfff8ee, 1.4);
    this.sunLight.position.set(14, 12, 18);
    this.scene.add(this.sunLight);

    // Earth Albedo bounce light
    this.earthAlbedo = new THREE.DirectionalLight(0x0077b6, 0.5);
    this.earthAlbedo.position.set(-12, -10, -10);
    this.scene.add(this.earthAlbedo);

    // Dynamic Plasma entry point light (emits fiery light during peak heating)
    this.plasmaLight = new THREE.PointLight(0xff6600, 0.0, 30);
    this.plasmaLight.position.set(0, -1, 0);
    this.scene.add(this.plasmaLight);

    // Pacific marine daylight fill light for splashdown and recovery operations
    this.marineHemiLight = new THREE.HemisphereLight(0xb0d7ff, 0x0b4168, 0.85);
    this.marineHemiLight.visible = false;
    this.scene.add(this.marineHemiLight);
  }

  _buildEarthLimb() {
    this.earthGroup = new THREE.Group();
    // Curved Earth segment positioned below spacecraft for atmospheric entry views
    const earthGeo = new THREE.SphereGeometry(65, 48, 32);

    // Dynamic Earth texture with oceans, continents and cloud layer
    const eCanvas = document.createElement('canvas');
    eCanvas.width = 1024;
    eCanvas.height = 512;
    const eCtx = eCanvas.getContext('2d');

    // Deep Pacific Ocean
    eCtx.fillStyle = '#0b2b52';
    eCtx.fillRect(0, 0, 1024, 512);

    // California / Baja coastline & North America
    eCtx.fillStyle = '#3a5335';
    eCtx.beginPath();
    eCtx.ellipse(650, 180, 140, 100, 0.3, 0, Math.PI * 2);
    eCtx.fill();
    eCtx.fillStyle = '#6b6045';
    eCtx.beginPath();
    eCtx.ellipse(680, 260, 45, 90, 0.45, 0, Math.PI * 2); // Baja Peninsula
    eCtx.fill();

    // Pacific Cloud Swirls
    eCtx.fillStyle = 'rgba(255, 255, 255, 0.45)';
    for (let c = 0; c < 20; c++) {
      const cx = (c * 52) % 1024;
      const cy = 80 + (c * 17) % 200;
      eCtx.beginPath();
      eCtx.arc(cx, cy, 25 + (c % 15) * 3, 0, Math.PI * 2);
      eCtx.fill();
    }

    const earthTex = new THREE.CanvasTexture(eCanvas);
    const earthMat = new THREE.MeshStandardMaterial({
      map: earthTex,
      roughness: 0.65,
      metalness: 0.1
    });

    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthMesh.rotation.x = Math.PI;
    this.earthMesh.position.set(-6, -64, -10);
    this.earthGroup.add(this.earthMesh);

    // Atmospheric Blue Limb Rim
    const atmoGeo = new THREE.SphereGeometry(66.2, 48, 24);
    const atmoMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.35,
      side: THREE.BackSide
    });
    this.atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
    this.atmoMesh.rotation.x = Math.PI;
    this.atmoMesh.position.set(-6, -64, -10);
    this.earthGroup.add(this.atmoMesh);

    // Starfield Points
    const starGeo = new THREE.BufferGeometry();
    const starCount = 600;
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starPositions[i] = (Math.random() - 0.5) * 300;
      starPositions[i + 1] = Math.random() * 150 + 10;
      starPositions[i + 2] = (Math.random() - 0.5) * 300;
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.8, transparent: true, opacity: 0.8 });
    this.starPoints = new THREE.Points(starGeo, starMat);
    this.earthGroup.add(this.starPoints);

    this.scene.add(this.earthGroup);
  }

  _buildCrewModule() {
    // Authentic Orion CM Conical Frustum (5.029m base, 3.35m height, 1.3m top hatch)
    const cmRadiusBase = 2.514;
    const cmRadiusTop = 0.65;
    const cmHeight = 3.35;

    // Generate dynamic Orion CM Texture with red NASA Worm Logo & American Flag
    const texCanvas = document.createElement('canvas');
    texCanvas.width = 1024;
    texCanvas.height = 512;
    const ctx = texCanvas.getContext('2d');

    // Charcoal black thermal tiles lower half
    ctx.fillStyle = '#1c2026';
    ctx.fillRect(0, 0, 1024, 512);

    // White thermal protection blanket upper half
    ctx.fillStyle = '#f0f3f6';
    ctx.fillRect(0, 0, 1024, 320);

    // Subtle tile seams
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.12)';
    ctx.lineWidth = 1;
    for (let x = 0; x < 1024; x += 32) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 512); ctx.stroke();
    }
    for (let y = 0; y < 512; y += 24) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(1024, y); ctx.stroke();
    }

    // Bold Red NASA Worm Logo
    ctx.fillStyle = '#e03a3e';
    ctx.font = '900 68px "Arial Black", sans-serif';
    ctx.fillText('NASA', 370, 200);

    // American Flag
    const flagX = 590, flagY = 150, flagW = 80, flagH = 48;
    for (let s = 0; s < 7; s++) {
      ctx.fillStyle = (s % 2 === 0) ? '#b22234' : '#ffffff';
      ctx.fillRect(flagX, flagY + s * (flagH / 7), flagW, flagH / 7);
    }
    ctx.fillStyle = '#3c3b6e';
    ctx.fillRect(flagX, flagY, flagW * 0.42, flagH * 0.55);

    // Forward hatch & pilot windows
    ctx.fillStyle = '#080c10';
    ctx.beginPath(); ctx.arc(512, 80, 24, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#00e5ff'; ctx.lineWidth = 2; ctx.stroke();

    const cmTex = new THREE.CanvasTexture(texCanvas);
    const cmGeom = new THREE.CylinderGeometry(cmRadiusTop, cmRadiusBase, cmHeight, 36);
    const cmMat = new THREE.MeshStandardMaterial({
      map: cmTex,
      metalness: 0.35,
      roughness: 0.45
    });

    this.cmMesh = new THREE.Mesh(cmGeom, cmMat);
    this.cmMesh.position.y = cmHeight / 2.0;
    this.spacecraftGroup.add(this.cmMesh);

    // Forward Bay Cover (jettisoned prior to drogue chute deployment)
    const fbcGeo = new THREE.CylinderGeometry(0.68, 0.85, 0.5, 24);
    const fbcMat = new THREE.MeshStandardMaterial({ color: 0x212529, roughness: 0.8 });
    this.fbcMesh = new THREE.Mesh(fbcGeo, fbcMat);
    this.fbcMesh.position.y = cmHeight + 0.25;
    this.spacecraftGroup.add(this.fbcMesh);

    // Twin Pilot Windows
    const winGeom = new THREE.BoxGeometry(0.38, 0.28, 0.08);
    const winMat = new THREE.MeshPhysicalMaterial({
      color: 0x050d1a,
      metalness: 0.95,
      roughness: 0.05,
      reflectivity: 0.9
    });
    const leftWin = new THREE.Mesh(winGeom, winMat);
    leftWin.position.set(-0.55, 2.25, 1.48);
    leftWin.rotation.set(-0.55, -0.25, 0.15);
    this.spacecraftGroup.add(leftWin);

    const rightWin = new THREE.Mesh(winGeom, winMat);
    rightWin.position.set(0.55, 2.25, 1.48);
    rightWin.rotation.set(-0.55, 0.25, -0.15);
    this.spacecraftGroup.add(rightWin);
  }

  _buildHeatShield() {
    // Convex Avcoat ablative heat shield (diameter 5.029m)
    const hsGeom = new THREE.SphereGeometry(3.6, 36, 16, 0, Math.PI * 2, 0, Math.PI * 0.24);
    this.hsMat = new THREE.MeshStandardMaterial({
      color: 0x8d5b4c, // Burnt Avcoat orange-brown honeycomb
      roughness: 0.88,
      metalness: 0.12
    });
    this.hsMesh = new THREE.Mesh(hsGeom, this.hsMat);
    this.hsMesh.rotation.x = Math.PI;
    this.hsMesh.position.y = 2.45;
    this.spacecraftGroup.add(this.hsMesh);
  }

  _buildServiceModule() {
    // European Service Module (ESM) Cylinder (5.0m dia, 4.0m height)
    const esmRadius = 2.50;
    const esmHeight = 4.00;
    const esmGeom = new THREE.CylinderGeometry(esmRadius, esmRadius, esmHeight, 36);
    const esmMat = new THREE.MeshStandardMaterial({
      color: 0xe0e6ed,
      metalness: 0.45,
      roughness: 0.35
    });
    this.esmMesh = new THREE.Mesh(esmGeom, esmMat);
    this.esmMesh.position.y = -(esmHeight / 2.0);
    this.esmGroup.add(this.esmMesh);

    // OMS-E AJ10-190 Main Engine Nozzle
    const nozzleGeom = new THREE.ConeGeometry(0.75, 1.45, 24, 1, true);
    const nozzleMat = new THREE.MeshStandardMaterial({
      color: 0x1f2421,
      metalness: 0.9,
      roughness: 0.2,
      side: THREE.DoubleSide
    });
    this.nozzleMesh = new THREE.Mesh(nozzleGeom, nozzleMat);
    this.nozzleMesh.position.y = -(esmHeight + 0.72);
    this.esmGroup.add(this.nozzleMesh);

    // Engine firing visual glow
    const glowGeom = new THREE.ConeGeometry(0.70, 1.35, 16);
    this.engineGlowMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.0
    });
    this.engineGlow = new THREE.Mesh(glowGeom, this.engineGlowMat);
    this.engineGlow.position.y = -(esmHeight + 0.72);
    this.esmGroup.add(this.engineGlow);

    // 4 Quad RCS Thruster Pods on ESM
    for (let i = 0; i < 4; i++) {
      const ang = (i * Math.PI) / 2.0 + Math.PI / 4.0;
      const podGroup = new THREE.Group();
      podGroup.position.set(Math.cos(ang) * (esmRadius + 0.1), -1.2, Math.sin(ang) * (esmRadius + 0.1));
      podGroup.rotation.y = -ang;

      const podBase = new THREE.Mesh(
        new THREE.BoxGeometry(0.3, 0.4, 0.25),
        new THREE.MeshStandardMaterial({ color: 0x90a4ae, metalness: 0.8, roughness: 0.2 })
      );
      podGroup.add(podBase);

      const nozGeo = new THREE.ConeGeometry(0.05, 0.12, 8);
      const nozMat = new THREE.MeshStandardMaterial({ color: 0x263238, metalness: 0.9 });
      const n1 = new THREE.Mesh(nozGeo, nozMat); n1.position.set(0.08, 0.1, 0.12); n1.rotation.x = Math.PI / 2;
      const n2 = new THREE.Mesh(nozGeo, nozMat); n2.position.set(-0.08, 0.1, 0.12); n2.rotation.x = Math.PI / 2;
      const n3 = new THREE.Mesh(nozGeo, nozMat); n3.position.set(0.08, -0.1, 0.12); n3.rotation.x = Math.PI / 2;
      const n4 = new THREE.Mesh(nozGeo, nozMat); n4.position.set(-0.08, -0.1, 0.12); n4.rotation.x = Math.PI / 2;
      podGroup.add(n1, n2, n3, n4);

      this.esmGroup.add(podGroup);
    }
  }

  _buildSolarArrays() {
    const esmRadius = 2.50;
    const esmHeight = 4.00;
    const angles = [Math.PI * 0.25, Math.PI * 0.75, Math.PI * 1.25, Math.PI * 1.75];

    const solCanvas = document.createElement('canvas');
    solCanvas.width = 256;
    solCanvas.height = 128;
    const sCtx = solCanvas.getContext('2d');
    sCtx.fillStyle = '#0a1628';
    sCtx.fillRect(0, 0, 256, 128);
    sCtx.strokeStyle = 'rgba(0, 229, 255, 0.25)';
    sCtx.lineWidth = 1;
    for (let x = 0; x < 256; x += 16) sCtx.strokeRect(x, 2, 14, 124);
    sCtx.strokeStyle = '#d48806'; sCtx.lineWidth = 2;
    sCtx.beginPath(); sCtx.moveTo(0, 64); sCtx.lineTo(256, 64); sCtx.stroke();
    const solTex = new THREE.CanvasTexture(solCanvas);

    for (let i = 0; i < 4; i++) {
      const wingPivot = new THREE.Group();
      wingPivot.position.set(0, -(esmHeight * 0.45), 0);
      wingPivot.rotation.y = angles[i];

      const boomGeom = new THREE.CylinderGeometry(0.06, 0.06, 1.2, 12);
      const boomMat = new THREE.MeshStandardMaterial({ color: 0x455a64, metalness: 0.8 });
      const boom = new THREE.Mesh(boomGeom, boomMat);
      boom.rotation.z = Math.PI * 0.5;
      boom.position.x = esmRadius + 0.6;
      wingPivot.add(boom);

      const panelGroup = new THREE.Group();
      panelGroup.position.x = esmRadius + 1.2;
      panelGroup.rotation.z = -0.22;

      for (let p = 0; p < 3; p++) {
        const panelGeom = new THREE.BoxGeometry(2.1, 0.04, 1.1);
        const panelMat = new THREE.MeshStandardMaterial({
          map: solTex,
          metalness: 0.85,
          roughness: 0.25
        });
        const panel = new THREE.Mesh(panelGeom, panelMat);
        panel.position.x = 1.1 + (p * 2.2);
        panelGroup.add(panel);
      }

      wingPivot.add(panelGroup);
      this.esmGroup.add(wingPivot);
      this.solarWings.push(panelGroup);
    }
  }

  _buildRCSThrusters() {
    const plumePositions = [
      [2.55, 0.8, 0.0],
      [-2.55, 0.8, 0.0],
      [0.0, 0.8, 2.55],
      [0.0, 0.8, -2.55]
    ];
    for (let pos of plumePositions) {
      const plumeGeom = new THREE.ConeGeometry(0.18, 0.55, 12);
      const plumeMat = new THREE.MeshBasicMaterial({
        color: 0x00e5ff,
        transparent: true,
        opacity: 0.0
      });
      const plume = new THREE.Mesh(plumeGeom, plumeMat);
      plume.position.set(...pos);
      this.spacecraftGroup.add(plume);
      this.rcsThrusters.push(plume);
    }
  }

  _buildReentryFeatures() {
    // -----------------------------------------------------------------------
    // 1. Hypersonic Plasma Bow Shock & Fiery Trailing Wake (25,000 MPH / 5,000°F)
    // Reference: NASA Artemis II Atmospheric Reentry Poster & Fact Sheet
    // -----------------------------------------------------------------------

    // A. Incandescent Bow Shock Envelope (curving tightly over Avcoat Heat Shield at y <= 0)
    const shockGeo = new THREE.SphereGeometry(3.68, 36, 16, 0, Math.PI * 2, 0, Math.PI * 0.26);
    this.plasmaMat = new THREE.MeshBasicMaterial({
      color: 0xff8c00, // Fiery orange shock fringe
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    this.plasmaMesh = new THREE.Mesh(shockGeo, this.plasmaMat);
    this.plasmaMesh.rotation.x = Math.PI;
    this.plasmaMesh.position.y = 2.45;
    this.spacecraftGroup.add(this.plasmaMesh);

    // Inner brilliant white-yellow stagnation core
    const coreGeo = new THREE.SphereGeometry(3.62, 36, 16, 0, Math.PI * 2, 0, Math.PI * 0.22);
    this.plasmaCoreMat = new THREE.MeshBasicMaterial({
      color: 0xfffae0, // White-hot peak heating stagnation layer
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    this.plasmaCoreMesh = new THREE.Mesh(coreGeo, this.plasmaCoreMat);
    this.plasmaCoreMesh.rotation.x = Math.PI;
    this.plasmaCoreMesh.position.y = 2.45;
    this.spacecraftGroup.add(this.plasmaCoreMesh);

    // B. Fiery Trailing Wake Flame Sheath (simulating 25,000 MPH trailing plasma trail behind CM)
    // The flames billow upwards and backwards from the heat shield base (y = 0.2, r = 2.65) to y = 16 (r = 6.4)
    const wakeGeo = new THREE.CylinderGeometry(6.4, 2.65, 16.0, 32, 4, true);
    this.wakeMat = new THREE.MeshBasicMaterial({
      color: 0xff3b00, // Roaring aerodynamic wake fire
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    this.wakeMesh = new THREE.Mesh(wakeGeo, this.wakeMat);
    this.wakeMesh.position.y = 8.2;
    this.spacecraftGroup.add(this.wakeMesh);

    // Inner bright gold core wake sheath
    const wakeCoreGeo = new THREE.CylinderGeometry(4.2, 2.35, 12.0, 24, 2, true);
    this.wakeCoreMat = new THREE.MeshBasicMaterial({
      color: 0xffba00,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    this.wakeCoreMesh = new THREE.Mesh(wakeCoreGeo, this.wakeCoreMat);
    this.wakeCoreMesh.position.y = 6.2;
    this.spacecraftGroup.add(this.wakeCoreMesh);

    // Dynamic Streamers / Trailing Plasma Tendrils
    this.streamersGroup = new THREE.Group();
    const streamerMat = new THREE.MeshBasicMaterial({
      color: 0xffea00,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    this.streamerMeshes = [];
    for (let s = 0; s < 6; s++) {
      const sAng = (s * Math.PI * 2) / 6;
      const sGeo = new THREE.CylinderGeometry(0.04, 0.18, 14.0, 4);
      const sMesh = new THREE.Mesh(sGeo, streamerMat);
      sMesh.position.set(Math.cos(sAng) * 3.4, 7.8, Math.sin(sAng) * 3.4);
      sMesh.rotation.x = Math.sin(sAng) * 0.12;
      sMesh.rotation.z = Math.cos(sAng) * 0.12;
      this.streamersGroup.add(sMesh);
      this.streamerMeshes.push(sMesh);
    }
    this.spacecraftGroup.add(this.streamersGroup);

    // C. Glowing Incandescence over Avcoat Heat Shield (up to 5,000°F / 2,760°C)
    const glowGeo = new THREE.SphereGeometry(3.62, 36, 16, 0, Math.PI * 2, 0, Math.PI * 0.24);
    this.hsGlowMat = new THREE.MeshBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide
    });
    this.hsGlowMesh = new THREE.Mesh(glowGeo, this.hsGlowMat);
    this.hsGlowMesh.rotation.x = Math.PI;
    this.hsGlowMesh.position.y = 2.45;
    this.spacecraftGroup.add(this.hsGlowMesh);

    // -----------------------------------------------------------------------
    // 2. High-Altitude Drogue Parachutes (2x White Conical Drogues)
    // -----------------------------------------------------------------------
    this.drogueGroup = new THREE.Group();
    const drogueMat = new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.8 });
    for (let i = 0; i < 2; i++) {
      const dMesh = new THREE.Mesh(new THREE.ConeGeometry(1.2, 2.6, 16), drogueMat);
      dMesh.position.set(i === 0 ? -1.6 : 1.6, 11.5, 0);
      dMesh.rotation.x = Math.PI;
      this.drogueGroup.add(dMesh);

      const lineGeo = new THREE.CylinderGeometry(0.015, 0.015, 7.8, 6);
      const lineMat = new THREE.MeshBasicMaterial({ color: 0xdddddd });
      const line = new THREE.Mesh(lineGeo, lineMat);
      line.position.set(i === 0 ? -0.8 : 0.8, 7.2, 0);
      this.drogueGroup.add(line);
    }
    this.drogueGroup.visible = false;
    this.spacecraftGroup.add(this.drogueGroup);

    // -----------------------------------------------------------------------
    // 3. 3x Main Parachutes with Authentic ORANGE & WHITE Alternating Ring-Sail Stripes
    // -----------------------------------------------------------------------
    this.mainChuteGroup = new THREE.Group();

    // Create high-detail radial orange and white striped ring-sail canvas texture
    const chuteTexCanvas = document.createElement('canvas');
    chuteTexCanvas.width = 512;
    chuteTexCanvas.height = 256;
    const cCtx = chuteTexCanvas.getContext('2d');
    const numGores = 24;
    const goreW = 512 / numGores;
    for (let g = 0; g < numGores; g++) {
      cCtx.fillStyle = (g % 2 === 0) ? '#ff4500' : '#ffffff';
      cCtx.fillRect(g * goreW, 0, goreW, 256);
    }
    // Ring-sail aerodynamic slot gaps
    cCtx.strokeStyle = 'rgba(20, 20, 20, 0.35)';
    cCtx.lineWidth = 3;
    for (let y = 35; y < 256; y += 45) {
      cCtx.beginPath(); cCtx.moveTo(0, y); cCtx.lineTo(512, y); cCtx.stroke();
    }
    const mainChuteTex = new THREE.CanvasTexture(chuteTexCanvas);
    const mainChuteMat = new THREE.MeshStandardMaterial({
      map: mainChuteTex,
      roughness: 0.75,
      metalness: 0.05,
      side: THREE.DoubleSide
    });

    const chuteOffsets = [
      { x: 0.0, y: 18.0, z: -3.8 },
      { x: -4.0, y: 17.0, z: 3.2 },
      { x: 4.0, y: 17.0, z: 3.2 }
    ];

    this.mainChuteMeshes = [];
    chuteOffsets.forEach((pos, idx) => {
      const canopyGroup = new THREE.Group();
      canopyGroup.position.set(pos.x, pos.y, pos.z);

      // Hemispherical ring-sail canopy (116 ft / 35.3m scale)
      const dome = new THREE.Mesh(
        new THREE.SphereGeometry(4.2, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.48),
        mainChuteMat
      );
      dome.rotation.x = Math.PI; // Opening faces downward
      canopyGroup.add(dome);

      // Suspension Riser Line Cluster (converging to CM forward bulkhead lugs)
      const riserMat = new THREE.MeshBasicMaterial({ color: 0xcccccc });
      for (let r = 0; r < 8; r++) {
        const ang = (r * Math.PI * 2) / 8;
        const rimX = Math.cos(ang) * 4.0;
        const rimZ = Math.sin(ang) * 4.0;

        const p1 = new THREE.Vector3(rimX, 0, rimZ);
        const p2 = new THREE.Vector3(-pos.x * 0.8, -pos.y + 3.8, -pos.z * 0.8);
        const dist = p1.distanceTo(p2);

        const rGeo = new THREE.CylinderGeometry(0.018, 0.018, dist, 4);
        const riserMesh = new THREE.Mesh(rGeo, riserMat);
        riserMesh.position.copy(p1.clone().add(p2).multiplyScalar(0.5));
        riserMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), p2.clone().sub(p1).normalize());
        canopyGroup.add(riserMesh);
      }

      this.mainChuteGroup.add(canopyGroup);
      this.mainChuteMeshes.push(canopyGroup);
    });

    this.mainChuteGroup.visible = false;
    this.spacecraftGroup.add(this.mainChuteGroup);

    // -----------------------------------------------------------------------
    // 4. Pacific Ocean Water Surface Mesh & Splash Foam Ring
    // -----------------------------------------------------------------------
    const oceanGeo = new THREE.PlaneGeometry(360, 360, 64, 64);
    const oceanMat = new THREE.MeshStandardMaterial({
      color: 0x0c4b78,
      roughness: 0.52,
      metalness: 0.12
    });
    this.oceanMesh = new THREE.Mesh(oceanGeo, oceanMat);
    this.oceanMesh.rotation.x = -Math.PI / 2;
    this.oceanMesh.position.y = 0.0;
    this.oceanMesh.visible = false;
    this.scene.add(this.oceanMesh);

    // Water Splash Foam Ring under capsule
    const foamGeo = new THREE.RingGeometry(1.6, 2.7, 36);
    const foamMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.40,
      side: THREE.DoubleSide
    });
    this.foamMesh = new THREE.Mesh(foamGeo, foamMat);
    this.foamMesh.rotation.x = -Math.PI / 2;
    this.foamMesh.position.y = 0.02;
    this.foamMesh.visible = false;
    this.scene.add(this.foamMesh);

    // -----------------------------------------------------------------------
    // 5. CMUS (Crew Module Uprighting System) 5 Orange Balloons & Flotation Collar
    // DIRECT CHILDREN OF spacecraftGroup so they stay firmly attached to the capsule!
    // Reference: NASA Fact Sheet "Orion Recovery Operations"
    // -----------------------------------------------------------------------
    this.cmusGroup = new THREE.Group();

    const cmusMat = new THREE.MeshStandardMaterial({
      color: 0xff3d00, // Vibrant international rescue orange matching NASA photos
      roughness: 0.35,
      metalness: 0.15
    });
    const strapMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const capMat = new THREE.MeshBasicMaterial({ color: 0x1a1a1a });

    this.cmusBalloons = [];
    for (let b = 0; b < 5; b++) {
      const bAng = (b * Math.PI * 2) / 5;
      const bx = Math.cos(bAng) * 0.52;
      const bz = Math.sin(bAng) * 0.52;

      const balloonGroup = new THREE.Group();
      balloonGroup.position.set(bx, 3.68, bz);

      // Egg / teardrop uprighting balloon geometry
      const balloonGeo = new THREE.SphereGeometry(0.44, 24, 16);
      const balloon = new THREE.Mesh(balloonGeo, cmusMat);
      balloon.scale.set(1.0, 1.25, 1.0);
      balloonGroup.add(balloon);

      // Top inflation cap
      const topCap = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.04, 12), capMat);
      topCap.position.y = 0.55;
      balloonGroup.add(topCap);

      // White structural reinforcement straps (radiating from top cap)
      const strap1 = new THREE.Mesh(new THREE.TorusGeometry(0.442, 0.012, 6, 24), strapMat);
      strap1.rotation.y = Math.PI / 4;
      balloonGroup.add(strap1);

      const strap2 = new THREE.Mesh(new THREE.TorusGeometry(0.442, 0.012, 6, 24), strapMat);
      strap2.rotation.y = -Math.PI / 4;
      balloonGroup.add(strap2);

      this.cmusGroup.add(balloonGroup);
      this.cmusBalloons.push(balloonGroup);
    }
    this.cmusGroup.visible = false;
    this.spacecraftGroup.add(this.cmusGroup);

    // Inflatable Flotation Collar (Neon Safety Lime-Yellow Torus around base waterline)
    const collarGeo = new THREE.TorusGeometry(2.55, 0.32, 16, 48);
    const collarMat = new THREE.MeshStandardMaterial({
      color: 0xc6ff00, // Safety neon yellow-green matching NASA diver collar
      roughness: 0.40,
      metalness: 0.15
    });
    this.collarMesh = new THREE.Mesh(collarGeo, collarMat);
    this.collarMesh.rotation.x = Math.PI / 2;
    this.collarMesh.position.y = 0.25; // Snug at base waterline
    this.collarMesh.visible = false;
    this.spacecraftGroup.add(this.collarMesh);

    // -----------------------------------------------------------------------
    // 6. Navy Recovery Team: Rigid Inflatable Boat (RHIB) & Divers
    // -----------------------------------------------------------------------
    this.rhibGroup = new THREE.Group();
    this.rhibGroup.position.set(5.5, 0.02, 3.2);
    this.rhibGroup.rotation.y = -0.60;

    // RHIB rubber collar hull
    const rhibHullMat = new THREE.MeshStandardMaterial({ color: 0x212529, roughness: 0.65 });
    const rhibTube = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.35, 12, 32), rhibHullMat);
    rhibTube.rotation.x = Math.PI / 2;
    rhibTube.scale.set(0.7, 1.8, 0.7);
    this.rhibGroup.add(rhibTube);

    // RHIB Deck floor
    const deckMesh = new THREE.Mesh(
      new THREE.BoxGeometry(2.0, 0.2, 5.5),
      new THREE.MeshStandardMaterial({ color: 0x37474f, roughness: 0.85 })
    );
    deckMesh.position.y = -0.1;
    this.rhibGroup.add(deckMesh);

    // Navy Crew / Divers (2 figures in helmets & orange drysuits)
    const diverMat = new THREE.MeshStandardMaterial({ color: 0xff5722, roughness: 0.5 });
    for (let d = 0; d < 2; d++) {
      const diver = new THREE.Group();
      diver.position.set(d === 0 ? -0.4 : 0.4, 0.6, d === 0 ? 0.3 : -0.8);
      const body = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.7, 10), diverMat);
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.18, 12, 10), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 }));
      head.position.y = 0.5;
      diver.add(body, head);
      this.rhibGroup.add(diver);
    }

    this.rhibGroup.visible = false;
    this.scene.add(this.rhibGroup);

    // Realistic arched tow line connecting Orion collar anchor to RHIB bow
    const towCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(2.1, 0.22, 1.25),
      new THREE.Vector3(3.4, 0.12, 2.05),
      new THREE.Vector3(4.7, 0.22, 2.85)
    ]);
    const towGeo = new THREE.TubeGeometry(towCurve, 20, 0.022, 6, false);
    const towMat = new THREE.MeshBasicMaterial({ color: 0xffeb3b }); // Hi-viz yellow recovery line
    this.towLine = new THREE.Mesh(towGeo, towMat);
    this.towLine.visible = false;
    this.scene.add(this.towLine);

    // -----------------------------------------------------------------------
    // 7. US Navy Amphibious Ship (USS Portland / LPD 27) in Background
    // Reference: NASA Fact Sheet "Artemis II Ocean Recovery"
    // -----------------------------------------------------------------------
    this.navyShipGroup = new THREE.Group();
    this.navyShipGroup.position.set(-22.0, -0.6, -26.0);
    this.navyShipGroup.rotation.y = 0.52;

    const shipHazeMat = new THREE.MeshStandardMaterial({ color: 0x546e7a, roughness: 0.75, metalness: 0.15 });
    const deckMat = new THREE.MeshStandardMaterial({ color: 0x263238, roughness: 0.90 });

    // Main Naval Hull (sunk realistically 0.6m into water)
    const shipHull = new THREE.Mesh(new THREE.BoxGeometry(8.5, 3.8, 28.0), shipHazeMat);
    shipHull.position.y = 1.0;
    this.navyShipGroup.add(shipHull);

    // Flight Deck aft plate
    const flightDeck = new THREE.Mesh(new THREE.BoxGeometry(8.0, 0.18, 13.0), deckMat);
    flightDeck.position.set(0, 2.95, 6.5);
    this.navyShipGroup.add(flightDeck);

    // Well deck stern gate notch
    const sternGate = new THREE.Mesh(new THREE.BoxGeometry(5.0, 1.8, 1.2), deckMat);
    sternGate.position.set(0, 1.6, 13.6);
    this.navyShipGroup.add(sternGate);

    // Superstructure & Bridge tower
    const bridge = new THREE.Mesh(new THREE.BoxGeometry(5.2, 4.2, 8.5), shipHazeMat);
    bridge.position.set(0, 4.8, -2.5);
    this.navyShipGroup.add(bridge);

    // Integrated Mast Structure
    const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.32, 6.5, 8), shipHazeMat);
    mast.position.set(0, 8.8, -2.5);
    this.navyShipGroup.add(mast);

    // Radar array sphere
    const radar = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 10), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 }));
    radar.position.set(0, 11.2, -2.5);
    this.navyShipGroup.add(radar);

    this.navyShipGroup.visible = false;
    this.scene.add(this.navyShipGroup);
  }

  setReentryPhase(phase) {
    this.currentPhase = phase;

    // Reset base positions
    this.spacecraftGroup.position.set(0, 0, 0);

    if (this.towLine) this.towLine.visible = (phase === 'recovery_ops');
    if (this.marineHemiLight) this.marineHemiLight.visible = (phase === 'splashdown' || phase === 'recovery_ops');

    if (phase === 'esm_jettison') {
      // 1. ESM Jettison & Separation
      this.esmGroup.visible = true;
      this.esmGroup.position.set(0, -6.5, 0); // Separated and falling away
      this.plasmaMat.opacity = 0.0;
      this.plasmaCoreMat.opacity = 0.0;
      this.wakeMat.opacity = 0.0;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.0;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.0);
      this.hsGlowMat.opacity = 0.0;
      this.plasmaLight.intensity = 0.0;
      this.fbcMesh.visible = true;
      this.drogueGroup.visible = false;
      this.mainChuteGroup.visible = false;
      this.cmusGroup.visible = false;
      this.collarMesh.visible = false;
      this.oceanMesh.visible = false;
      this.foamMesh.visible = false;
      this.rhibGroup.visible = false;
      this.navyShipGroup.visible = false;
      this.earthGroup.visible = true;
      this.spacecraftGroup.rotation.set(0.45, -0.4, 0.2);
      this.camera.position.set(16, 9, 20);
      if (this.controls) this.controls.target.set(0, 0, 0);

    } else if (phase === 'entry_interface') {
      // 2. Entry Interface (EI-400, 25,000 MPH / Mach 32.4)
      this.esmGroup.visible = false;
      this.plasmaMat.opacity = 0.55;
      this.plasmaCoreMat.opacity = 0.50;
      this.wakeMat.opacity = 0.45;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.50;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.40);
      this.hsGlowMat.opacity = 0.60;
      this.plasmaLight.intensity = 2.0;
      this.plasmaLight.color.setHex(0xff7700);
      this.fbcMesh.visible = true;
      this.drogueGroup.visible = false;
      this.mainChuteGroup.visible = false;
      this.cmusGroup.visible = false;
      this.collarMesh.visible = false;
      this.oceanMesh.visible = false;
      this.foamMesh.visible = false;
      this.rhibGroup.visible = false;
      this.navyShipGroup.visible = false;
      this.earthGroup.visible = true;
      // Reentry attitude: blunt heat shield down-forward, flames trailing up-backward
      this.spacecraftGroup.rotation.set(-0.35, 0.40, -0.60);
      this.camera.position.set(11.0, 3.5, 16.5);
      if (this.controls) this.controls.target.set(0, 1.2, 0);

    } else if (phase === 'peak_heating') {
      // 3. Peak Heating & Exo-Atmospheric Skip (5,000°F / 2,760°C)
      this.esmGroup.visible = false;
      this.plasmaMat.opacity = 0.85;
      this.plasmaCoreMat.opacity = 0.90;
      this.wakeMat.opacity = 0.80;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.85;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.75);
      this.hsGlowMat.opacity = 1.0;
      this.plasmaLight.intensity = 5.0;
      this.plasmaLight.color.setHex(0xffaa00);
      this.fbcMesh.visible = true;
      this.drogueGroup.visible = false;
      this.mainChuteGroup.visible = false;
      this.cmusGroup.visible = false;
      this.collarMesh.visible = false;
      this.oceanMesh.visible = false;
      this.foamMesh.visible = false;
      this.rhibGroup.visible = false;
      this.navyShipGroup.visible = false;
      this.earthGroup.visible = true;
      // High-angle skip lift vector, flames billowing upward
      this.spacecraftGroup.rotation.set(-0.38, 0.45, -0.65);
      this.camera.position.set(10.5, 3.2, 15.5);
      if (this.controls) this.controls.target.set(0, 1.2, 0);

    } else if (phase === 'drogue_chutes') {
      // 4. Drogue Parachutes (7.6 km down to 2.9 km)
      this.esmGroup.visible = false;
      this.plasmaMat.opacity = 0.0;
      this.plasmaCoreMat.opacity = 0.0;
      this.wakeMat.opacity = 0.0;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.0;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.0);
      this.hsGlowMat.opacity = 0.0;
      this.plasmaLight.intensity = 0.0;
      this.fbcMesh.visible = false; // Forward bay cover jettisoned
      this.drogueGroup.visible = true;
      this.mainChuteGroup.visible = false;
      this.cmusGroup.visible = false;
      this.collarMesh.visible = false;
      this.oceanMesh.visible = true;
      this.oceanMesh.position.y = -35.0;
      this.foamMesh.visible = false;
      this.rhibGroup.visible = false;
      this.navyShipGroup.visible = false;
      this.earthGroup.visible = true;
      this.spacecraftGroup.rotation.set(0.08, 0.0, 0.05);
      this.camera.position.set(16, 10, 20);
      if (this.controls) this.controls.target.set(0, 4.5, 0);

    } else if (phase === 'main_chutes') {
      // 5. 3x Main Parachutes with Orange & White Striped Ring-Sail Canopies
      this.esmGroup.visible = false;
      this.plasmaMat.opacity = 0.0;
      this.plasmaCoreMat.opacity = 0.0;
      this.wakeMat.opacity = 0.0;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.0;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.0);
      this.hsGlowMat.opacity = 0.0;
      this.plasmaLight.intensity = 0.0;
      this.fbcMesh.visible = false;
      this.drogueGroup.visible = false;
      this.mainChuteGroup.visible = true;
      this.cmusGroup.visible = false;
      this.collarMesh.visible = false;
      this.oceanMesh.visible = true; // Approaching Pacific water
      this.oceanMesh.position.y = -18.0;
      this.foamMesh.visible = false;
      this.rhibGroup.visible = false;
      this.navyShipGroup.visible = false;
      this.earthGroup.visible = false;
      this.spacecraftGroup.rotation.set(0.05, 0.0, 0.02);
      this.camera.position.set(20, 13, 26);
      if (this.controls) this.controls.target.set(0, 7.5, 0);

    } else if (phase === 'splashdown') {
      // 6. Pacific Ocean Splashdown (CMUS 5 Orange Balloons & Flotation Collar)
      this.esmGroup.visible = false;
      this.plasmaMat.opacity = 0.0;
      this.plasmaCoreMat.opacity = 0.0;
      this.wakeMat.opacity = 0.0;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.0;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.0);
      this.hsGlowMat.opacity = 0.0;
      this.plasmaLight.intensity = 0.0;
      this.fbcMesh.visible = false;
      this.drogueGroup.visible = false;
      this.mainChuteGroup.visible = false;
      this.cmusGroup.visible = true;
      this.collarMesh.visible = true;
      this.oceanMesh.visible = true;
      this.oceanMesh.position.y = 0.0;
      this.foamMesh.visible = true;
      this.rhibGroup.visible = false;
      this.navyShipGroup.visible = false;
      this.earthGroup.visible = false;
      this.spacecraftGroup.position.set(0, 0.08, 0); // Floating firmly at waterline
      this.spacecraftGroup.rotation.set(0.04, 0.35, 0.02);
      this.camera.position.set(8.5, 3.8, 11.5);
      if (this.controls) this.controls.target.set(0, 1.2, 0);

    } else if (phase === 'recovery_ops') {
      // 7. NASA & US Navy Recovery Operations (USS Portland & RHIB Divers)
      this.esmGroup.visible = false;
      this.plasmaMat.opacity = 0.0;
      this.plasmaCoreMat.opacity = 0.0;
      this.wakeMat.opacity = 0.0;
      if (this.wakeCoreMat) this.wakeCoreMat.opacity = 0.0;
      if (this.streamerMeshes) this.streamerMeshes.forEach(m => m.material.opacity = 0.0);
      this.hsGlowMat.opacity = 0.0;
      this.plasmaLight.intensity = 0.0;
      this.fbcMesh.visible = false;
      this.drogueGroup.visible = false;
      this.mainChuteGroup.visible = false;
      this.cmusGroup.visible = true;
      this.collarMesh.visible = true;
      this.oceanMesh.visible = true;
      this.oceanMesh.position.y = 0.0;
      this.foamMesh.visible = true;
      this.rhibGroup.visible = true;
      this.navyShipGroup.visible = true;
      this.earthGroup.visible = false;
      this.spacecraftGroup.position.set(0, 0.08, 0);
      this.spacecraftGroup.rotation.set(0.04, 0.35, 0.02);
      this.camera.position.set(13.5, 4.8, 16.5);
      if (this.controls) this.controls.target.set(1.0, 1.0, 0.5);
    }

    if (this.controls) this.controls.update();
    this._onWindowResize();
  }

  updateOrientation(quaternionArray, rcsFiringFlags, omseThrustN, solarTiltDeg, isESMAttached = true) {
    if (this.esmGroup && this.currentPhase === 'entry_interface') {
      this.esmGroup.visible = Boolean(isESMAttached);
    }

    if (quaternionArray && quaternionArray.length >= 4 && !this.mainChuteGroup.visible && !this.recoveryGroup.visible) {
      const targetQ = new THREE.Quaternion(
        quaternionArray[1],
        quaternionArray[2],
        quaternionArray[3],
        quaternionArray[0]
      );
      this.spacecraftGroup.quaternion.slerp(targetQ, 0.25);
    }

    if (isESMAttached && this.solarWings.length > 0) {
      const tiltRad = THREE.MathUtils.degToRad(solarTiltDeg || 0.0);
      for (let wing of this.solarWings) wing.rotation.y = tiltRad;
    }

    if (this.engineGlowMat) {
      this.engineGlowMat.opacity = (isESMAttached && omseThrustN > 100.0) ? 0.85 : 0.0;
    }

    if (rcsFiringFlags && this.rcsThrusters.length > 0) {
      for (let i = 0; i < this.rcsThrusters.length; i++) {
        const active = rcsFiringFlags[i % rcsFiringFlags.length];
        this.rcsThrusters[i].material.opacity = active ? 0.9 : 0.0;
      }
    }
  }

  _onWindowResize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    this.width = parent ? parent.clientWidth : (this.canvas.clientWidth || 340);
    this.height = parent ? parent.clientHeight : (this.canvas.clientHeight || 280);
    this.camera.aspect = this.width / Math.max(1, this.height);
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }

  _animate() {
    requestAnimationFrame(() => this._animate());

    this.simTime += 0.016;

    // 1. Parachute Billowing & Realistic Aerodynamic Pendular Sway
    if (this.mainChuteGroup && this.mainChuteGroup.visible) {
      const swayX = Math.sin(this.simTime * 1.6) * 0.04;
      const swayZ = Math.cos(this.simTime * 1.3) * 0.03;
      this.mainChuteGroup.rotation.z = swayX;
      this.mainChuteGroup.rotation.x = swayZ;

      // Subtle individual canopy breathe/oscillation
      if (this.mainChuteMeshes) {
        this.mainChuteMeshes.forEach((c, idx) => {
          const breathe = 1.0 + Math.sin(this.simTime * 2.2 + idx) * 0.02;
          c.scale.set(breathe, 1.0, breathe);
        });
      }
    }

    // 2. Drogue Chute Flutter
    if (this.drogueGroup && this.drogueGroup.visible) {
      this.drogueGroup.rotation.z = Math.sin(this.simTime * 3.5) * 0.06;
      this.drogueGroup.rotation.x = Math.cos(this.simTime * 4.0) * 0.05;
    }

    // 3. Hypersonic Plasma Wake Pulsing & Sparkle (25,000 MPH / 5,000°F)
    if (this.plasmaMat && this.plasmaMat.opacity > 0.1) {
      const pulse = Math.sin(this.simTime * 14.0) * 0.08;
      if (this.plasmaMesh) this.plasmaMesh.scale.set(1.0 + pulse * 0.5, 1.0 + pulse * 0.8, 1.0 + pulse * 0.5);
      if (this.wakeMesh) this.wakeMesh.scale.set(1.0 + pulse * 0.4, 1.0 + Math.sin(this.simTime * 10.0) * 0.06, 1.0 + pulse * 0.4);
      if (this.wakeCoreMesh) this.wakeCoreMesh.scale.set(1.0 + pulse * 0.6, 1.0 + Math.cos(this.simTime * 12.0) * 0.08, 1.0 + pulse * 0.6);
      if (this.streamersGroup) this.streamersGroup.rotation.y += 0.03;
    }

    // 4. Pacific Ocean Water Bobbing (Splashdown & Recovery Operations)
    if (this.oceanMesh && this.oceanMesh.visible && (this.currentPhase === 'splashdown' || this.currentPhase === 'recovery_ops')) {
      const wave = Math.sin(this.simTime * 1.5) * 0.04;
      this.spacecraftGroup.position.y = 0.08 + wave;
      this.spacecraftGroup.rotation.z = Math.sin(this.simTime * 1.1) * 0.02;
      this.spacecraftGroup.rotation.x = Math.cos(this.simTime * 1.3) * 0.02;

      if (this.foamMesh) {
        this.foamMesh.scale.set(1.0 + wave * 0.8, 1.0 + wave * 0.8, 1.0);
      }

      if (this.rhibGroup && this.rhibGroup.visible) {
        this.rhibGroup.position.y = 0.05 + Math.sin(this.simTime * 1.5 + 0.5) * 0.035;
        this.rhibGroup.rotation.z = Math.cos(this.simTime * 1.2) * 0.025;
      }
    }

    if (this.controls) this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

// Global auto-instantiation (only if not already created by dashboard.js)
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('spacecraftCanvas') && !window.spacecraftViewer) {
      window.spacecraftViewer = new OrionSpacecraft3D('spacecraftCanvas');
    }
  });
}
