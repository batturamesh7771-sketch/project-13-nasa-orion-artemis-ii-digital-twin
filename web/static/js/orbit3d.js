/**
 * NASA Orion MPCV Digital Twin — 3D Earth-Moon Mission Trajectory Visualizer
 * Real-time Three.js rendering matching the official NASA Artemis II Mission Profile:
 *   - Photorealistic Blue Marble Earth with atmosphere & rotation
 *   - Cratered Moon with dark maria & synchronous tidal positioning
 *   - Continuous End-to-End Artemis II Free-Return Trajectory:
 *       1. Earth Orbit / TLI Departure (Cyan track)
 *       2. Outbound Translunar Coast with directional vectors
 *       3. Circum-Lunar Flyby behind Moon farside (Electric Blue track)
 *       4. Trans-Earth Return Coast with Earthward vectors (Yellow dashed track)
 *       5. Atmospheric Re-entry Skip & Pacific Ocean Splashdown (Green track)
 *   - In-situ 3D Orion Spacecraft following the active trajectory through all 168 hours
 *   - Stage-dependent vehicle configuration: ESM & Solar Arrays jettisoned before entry!
 *   - 3D milestone callouts: Earth, TLI, Moon, Flyby, Return, Entry Interface, Splashdown
 *   - Camera presets: Overview, Earth Focus, Moon Focus, Spacecraft Chase Cam
 */

class OrionOrbit3D {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.container = this.canvas.parentElement;
    const cw = this.container ? this.container.clientWidth : 0;
    const ch = this.container ? this.container.clientHeight : 0;
    this.width = cw > 50 ? cw : (this.canvas.clientWidth > 50 ? this.canvas.clientWidth : 960);
    this.height = ch > 50 ? ch : (this.canvas.clientHeight > 50 ? this.canvas.clientHeight : 540);

    this.scene = new THREE.Scene();
    
    // Perspective Camera: Framed horizontally for Earth (left) and Moon (right)
    this.camera3D = new THREE.PerspectiveCamera(38, this.width / this.height, 1, 3000);
    this.camera3D.position.set(10, 18, 175);

    // 2D Orthographic Camera
    const aspect = this.width / this.height;
    const viewSize = 100;
    this.camera2D = new THREE.OrthographicCamera(
      -viewSize * aspect, viewSize * aspect,
      viewSize, -viewSize,
      1, 2000
    );
    this.camera2D.position.set(10, 220, 0);
    this.camera2D.lookAt(10, 0, 0);

    this.is2DMode = false;
    this.camera = this.camera3D;

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
      this.controls.target.set(8, 5, 0);
      this.controls.maxDistance = 500;
      this.controls.minDistance = 35;
    }

    // Geometry layout in scene coordinates
    this.earthPos = new THREE.Vector3(-42, -2, 0);
    this.moonPos = new THREE.Vector3(56, 12, -6);
    this.earthRadius = 17.0;
    this.moonRadius = 5.0;

    this.calloutData = [
      { id: 'calloutEarth', pos: new THREE.Vector3(-42, 22, 0), text: '<strong>Earth</strong><br>R = 6,378 km', class: 'callout-earth' },
      { id: 'calloutTLI', pos: new THREE.Vector3(-18, 20, 0), text: '<strong>TLI BURN</strong><br>T+ 25:14:00', class: 'callout-tli' },
      { id: 'calloutMoon', pos: new THREE.Vector3(52, 24, -6), text: '<strong>Moon</strong><br>R = 1,737 km', class: 'callout-moon' },
      { id: 'calloutFlyby', pos: new THREE.Vector3(72, 20, -6), text: '<strong>Lunar Flyby</strong><br>T+ 71:00:00 &bull; Perilune', class: 'callout-flyby' },
      { id: 'calloutReturn', pos: new THREE.Vector3(0, -18, 0), text: '<strong>Return Trajectory</strong><br>T+ 72:30:00 &bull; Free Return', class: 'callout-return' },
      { id: 'calloutReentry', pos: new THREE.Vector3(-33, -16, 0), text: '<strong>Entry Interface (EI-400)</strong><br>T+ 160:00:00 &bull; 122 km', class: 'callout-reentry' }
    ];

    this._initLighting();
    this._buildEarth();
    this._buildMoon();
    this._buildTrajectory();
    this._buildInSituOrion();
    this._buildCompass();
    this._initCalloutDOM();

    window.addEventListener('resize', () => this._onWindowResize());
    this._animate();
  }

  _initLighting() {
    const ambient = new THREE.AmbientLight(0xffffff, 0.55);
    this.scene.add(ambient);

    // Directional Sun lighting from deep space
    const sunLight = new THREE.DirectionalLight(0xfff8ee, 1.8);
    sunLight.position.set(200, 100, 150);
    this.scene.add(sunLight);

    // Atmospheric rim light
    const rimLight = new THREE.DirectionalLight(0x0084ff, 0.45);
    rimLight.position.set(-200, -80, -100);
    this.scene.add(rimLight);
  }

  _buildEarth() {
    const loader = new THREE.TextureLoader();
    const texture = loader.load(
      '/static/textures/earth_map.png',
      () => this.renderer.render(this.scene, this.camera),
      undefined,
      () => {}
    );
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;

    const geom = new THREE.SphereGeometry(this.earthRadius, 64, 64);
    const mat = new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.82,
      metalness: 0.05
    });

    this.earthMesh = new THREE.Mesh(geom, mat);
    this.earthMesh.position.copy(this.earthPos);
    this.earthMesh.rotation.y = 1.2;
    this.scene.add(this.earthMesh);

    // Atmospheric cyan glow
    const glowGeom = new THREE.SphereGeometry(this.earthRadius + 0.9, 36, 36);
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x48cae4,
      transparent: true,
      opacity: 0.22,
      side: THREE.BackSide
    });
    const glow = new THREE.Mesh(glowGeom, glowMat);
    glow.position.copy(this.earthPos);
    this.scene.add(glow);
  }

  _buildMoon() {
    const loader = new THREE.TextureLoader();
    const texture = loader.load(
      '/static/textures/moon_map.png',
      () => this.renderer.render(this.scene, this.camera),
      undefined,
      () => {}
    );

    const geom = new THREE.SphereGeometry(this.moonRadius, 36, 36);
    const mat = new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.85,
      metalness: 0.05
    });

    this.moonMesh = new THREE.Mesh(geom, mat);
    this.moonMesh.position.copy(this.moonPos);
    this.scene.add(this.moonMesh);
  }

  _buildTrajectory() {
    // -------------------------------------------------------------------------
    // 1. OUTBOUND TRANSLUNAR COAST (Cyan solid curve with forward directional arrows)
    // -------------------------------------------------------------------------
    this.outboundCurve = new THREE.CubicBezierCurve3(
      new THREE.Vector3(this.earthPos.x + 8, this.earthPos.y + 12, 0),
      new THREE.Vector3(-10, 26, 0),
      new THREE.Vector3(30, 20, -5),
      new THREE.Vector3(this.moonPos.x - 2, this.moonPos.y + 7, -6)
    );

    const outPts = this.outboundCurve.getPoints(80);
    const outGeom = new THREE.BufferGeometry().setFromPoints(outPts);
    const outMat = new THREE.LineBasicMaterial({
      color: 0x00e5ff,
      linewidth: 2.5
    });
    this.outboundLine = new THREE.Line(outGeom, outMat);
    this.scene.add(this.outboundLine);

    // Outbound directional arrows pointing to Moon
    const arrowGeom = new THREE.ConeGeometry(0.8, 2.2, 8);
    const arrowMat = new THREE.MeshBasicMaterial({ color: 0x00e676 });
    [0.25, 0.65].forEach(t => {
      const pt = this.outboundCurve.getPoint(t);
      const tangent = this.outboundCurve.getTangent(t).normalize();
      const arrow = new THREE.Mesh(arrowGeom, arrowMat);
      arrow.position.copy(pt);
      arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      this.scene.add(arrow);
    });

    // -------------------------------------------------------------------------
    // 2. LUNAR FLYBY PERICYNTHION LOOP (Electric Blue arc swinging behind Moon far side)
    // -------------------------------------------------------------------------
    this.flybySpline = new THREE.CatmullRomCurve3([
      new THREE.Vector3(this.moonPos.x - 2, this.moonPos.y + 7, -6),
      new THREE.Vector3(this.moonPos.x + 8, this.moonPos.y + 6, -7),
      new THREE.Vector3(this.moonPos.x + 12, this.moonPos.y, -6),
      new THREE.Vector3(this.moonPos.x + 8, this.moonPos.y - 6, -5),
      new THREE.Vector3(this.moonPos.x - 3, this.moonPos.y - 6, -6)
    ]);

    const flybyPts = this.flybySpline.getPoints(60);
    const flybyGeom = new THREE.BufferGeometry().setFromPoints(flybyPts);
    const flybyMat = new THREE.LineBasicMaterial({
      color: 0x0084ff,
      linewidth: 2.5
    });
    this.flybyLine = new THREE.Line(flybyGeom, flybyMat);
    this.scene.add(this.flybyLine);

    // -------------------------------------------------------------------------
    // 3. INBOUND RETURN TRAJECTORY (Yellow dashed curve returning to Earth)
    // -------------------------------------------------------------------------
    this.returnCurve = new THREE.CubicBezierCurve3(
      new THREE.Vector3(this.moonPos.x - 3, this.moonPos.y - 6, -6),
      new THREE.Vector3(32, -14, -5),
      new THREE.Vector3(0, -22, -2),
      new THREE.Vector3(this.earthPos.x + 8, this.earthPos.y - 10, 0)
    );

    const inPts = this.returnCurve.getPoints(80);
    const inGeom = new THREE.BufferGeometry().setFromPoints(inPts);
    const inMat = new THREE.LineDashedMaterial({
      color: 0xffd600,
      dashSize: 3.5,
      gapSize: 2.0,
      linewidth: 2
    });
    this.inboundLine = new THREE.Line(inGeom, inMat);
    this.inboundLine.computeLineDistances();
    this.scene.add(this.inboundLine);

    // Return directional arrows pointing to Earth
    const retArrowMat = new THREE.MeshBasicMaterial({ color: 0xffd600 });
    [0.35, 0.75].forEach(t => {
      const pt = this.returnCurve.getPoint(t);
      const tangent = this.returnCurve.getTangent(t).normalize();
      const arrow = new THREE.Mesh(arrowGeom, retArrowMat);
      arrow.position.copy(pt);
      arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      this.scene.add(arrow);
    });

    // -------------------------------------------------------------------------
    // 4. ATMOSPHERIC SKIP REENTRY & SPLASHDOWN (Atmospheric arc curving into Pacific)
    // -------------------------------------------------------------------------
    this.reentryCurve = new THREE.CubicBezierCurve3(
      new THREE.Vector3(this.earthPos.x + 8, this.earthPos.y - 10, 0),
      new THREE.Vector3(this.earthPos.x + 4, this.earthPos.y - 6, 0),
      new THREE.Vector3(this.earthPos.x + 3, this.earthPos.y + 2, 0),
      new THREE.Vector3(this.earthPos.x + 5, this.earthPos.y + 6, 0)
    );

    const rePts = this.reentryCurve.getPoints(30);
    const reGeom = new THREE.BufferGeometry().setFromPoints(rePts);
    const reMat = new THREE.LineBasicMaterial({
      color: 0x00e676,
      linewidth: 2.5
    });
    this.reentryLine = new THREE.Line(reGeom, reMat);
    this.scene.add(this.reentryLine);

    // Splashdown Marker Beacon in Pacific
    const splashGeom = new THREE.RingGeometry(0.8, 1.4, 16);
    const splashMat = new THREE.MeshBasicMaterial({
      color: 0x00e676,
      side: THREE.DoubleSide
    });
    this.splashBeacon = new THREE.Mesh(splashGeom, splashMat);
    this.splashBeacon.position.copy(new THREE.Vector3(this.earthPos.x + 5, this.earthPos.y + 6, 0));
    this.scene.add(this.splashBeacon);
  }

  _buildInSituOrion() {
    // 3D Orion Spacecraft Group placed along the trajectory
    this.scGroup = new THREE.Group();

    // Crew Module (White/silver cone)
    const cmGeom = new THREE.ConeGeometry(1.6, 2.0, 16);
    const cmMat = new THREE.MeshStandardMaterial({
      color: 0xe0e6ed,
      roughness: 0.3,
      metalness: 0.8
    });
    this.cmMesh = new THREE.Mesh(cmGeom, cmMat);
    this.cmMesh.rotation.z = Math.PI / 2;
    this.scGroup.add(this.cmMesh);

    // Heat Shield on CM base
    const hsGeom = new THREE.SphereGeometry(1.62, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.35);
    const hsMat = new THREE.MeshStandardMaterial({ color: 0x4a3728, roughness: 0.9, metalness: 0.1 });
    this.hsMesh = new THREE.Mesh(hsGeom, hsMat);
    this.hsMesh.rotation.z = -Math.PI / 2;
    this.hsMesh.position.set(-0.95, 0, 0);
    this.scGroup.add(this.hsMesh);

    // Service Module Group (jettisoned before atmospheric reentry)
    this.esmGroup = new THREE.Group();

    const smGeom = new THREE.CylinderGeometry(1.5, 1.5, 2.2, 16);
    const smMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.4,
      metalness: 0.5
    });
    this.smMesh = new THREE.Mesh(smGeom, smMat);
    this.smMesh.position.set(-1.8, 0, 0);
    this.smMesh.rotation.z = Math.PI / 2;
    this.esmGroup.add(this.smMesh);

    // 4 Solar Array Wings in X-formation (glowing blue)
    const solarMat = new THREE.MeshStandardMaterial({
      color: 0x0084ff,
      roughness: 0.2,
      metalness: 0.9,
      emissive: 0x003366
    });

    const wingGeom = new THREE.BoxGeometry(0.4, 3.6, 0.08);
    this.solarWings = [];
    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI / 2) + Math.PI / 4;
      const wing = new THREE.Mesh(wingGeom, solarMat);
      wing.position.set(-1.8, Math.sin(angle) * 2.8, Math.cos(angle) * 2.8);
      wing.rotation.x = angle;
      this.esmGroup.add(wing);
      this.solarWings.push(wing);
    }

    this.scGroup.add(this.esmGroup);

    // Initial position along outbound track
    this.updateSpacecraftPosition(0.08);
    this.scene.add(this.scGroup);
  }

  _buildCompass() {
    this.compassGroup = new THREE.Group();
    const axisLen = 6.0;
    
    // X (Red)
    const xGeom = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(axisLen,0,0)]);
    this.compassGroup.add(new THREE.Line(xGeom, new THREE.LineBasicMaterial({ color: 0xff1744, linewidth: 2 })));
    
    // Y (Green)
    const yGeom = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(0,axisLen,0)]);
    this.compassGroup.add(new THREE.Line(yGeom, new THREE.LineBasicMaterial({ color: 0x00e676, linewidth: 2 })));
    
    // Z (Blue)
    const zGeom = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,axisLen)]);
    this.compassGroup.add(new THREE.Line(zGeom, new THREE.LineBasicMaterial({ color: 0x0084ff, linewidth: 2 })));

    this.compassGroup.position.set(50, -22, 10);
    this.scene.add(this.compassGroup);
  }

  _initCalloutDOM() {
    const wrapper = this.canvas.parentElement;
    if (!wrapper) return;

    this.calloutElements = [];
    this.calloutData.forEach(item => {
      let el = wrapper.querySelector(`.${item.class}`);
      if (!el) {
        el = document.createElement('div');
        el.className = `callout ${item.class}`;
        wrapper.appendChild(el);
      }
      el.innerHTML = item.text;
      this.calloutElements.push({ el, pos: item.pos });
    });
  }

  _updateCallouts() {
    if (!this.calloutElements || !this.container) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    if (w <= 0 || h <= 0) {
      this.calloutElements.forEach(item => { item.el.style.display = 'none'; });
      return;
    }

    this.calloutElements.forEach(item => {
      const v = item.pos.clone().project(this.camera);
      const x = (v.x * 0.5 + 0.5) * w;
      const y = (-(v.y * 0.5) + 0.5) * h;

      if (v.z < 1.0) {
        item.el.style.display = 'block';
        item.el.style.left = `${Math.round(x)}px`;
        item.el.style.top = `${Math.round(y)}px`;
      } else {
        item.el.style.display = 'none';
      }
    });
  }

  set2DMode(enabled) {
    this.is2DMode = enabled;
    this.camera = enabled ? this.camera2D : this.camera3D;
    if (this.controls) {
      this.controls.object = this.camera;
      this.controls.enableRotate = !enabled;
    }
  }

  setCameraPreset(name) {
    if (!this.controls) return;
    if (name === 'earth') {
      this.controls.target.copy(this.earthPos);
      this.camera3D.position.set(this.earthPos.x, this.earthPos.y + 20, 80);
    } else if (name === 'moon') {
      this.controls.target.copy(this.moonPos);
      this.camera3D.position.set(this.moonPos.x, this.moonPos.y + 10, 45);
    } else if (name === 'spacecraft' && this.scGroup) {
      this.controls.target.copy(this.scGroup.position);
      this.camera3D.position.set(this.scGroup.position.x + 15, this.scGroup.position.y + 10, this.scGroup.position.z + 25);
    } else {
      // Default overview
      this.controls.target.set(8, 5, 0);
      this.camera3D.position.set(10, 18, 175);
    }
    this.controls.update();
  }

  /**
   * Sample the complete 168-hour Artemis II mission path:
   *   0.00 to 0.05: Earth Orbit Insertion (around Earth)
   *   0.05 to 0.44: Outbound Translunar Coast (TLI to Moon approach)
   *   0.44 to 0.54: Circum-Lunar Flyby (behind Moon farside at perilune)
   *   0.54 to 0.94: Trans-Earth Return Coast (Moon to Earth return)
   *   0.94 to 0.99: Atmospheric Skip Reentry (EI-400 to drogues)
   *   0.99 to 1.00: Pacific Ocean Splashdown
   */
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
      const esmAttached = (u < 0.96); // ESM jettisoned right before entry interface!
      return { pos, tangent, stage: 'TRANS_EARTH_RETURN', esmAttached };
    } else {
      // Phase 7 & 8: Atmospheric Reentry & Splashdown
      const u = (f - 0.94) / (1.0 - 0.94);
      const pos = this.reentryCurve.getPoint(u);
      const tangent = this.reentryCurve.getTangent(u).normalize();
      return { pos, tangent, stage: 'REENTRY_SPLASHDOWN', esmAttached: false };
    }
  }

  updateSpacecraftPosition(tFrac) {
    if (!this.scGroup) return;
    const { pos, tangent, stage, esmAttached } = this.getMissionPositionAndTangent(tFrac);

    this.scGroup.position.copy(pos);
    this.scGroup.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), tangent);

    // Stage-dependent jettison: Hide European Service Module during atmospheric re-entry
    if (this.esmGroup) {
      this.esmGroup.visible = esmAttached;
    }

    // Orient heat shield forward when entering atmosphere
    if (stage === 'REENTRY_SPLASHDOWN') {
      // During reentry, blunt heat shield flies into velocity vector
      this.scGroup.quaternion.setFromUnitVectors(new THREE.Vector3(-1, 0, 0), tangent);
    }
  }

  _onWindowResize() {
    if (!this.canvas || !this.container) return;
    const cw = this.container.clientWidth || this.canvas.clientWidth;
    const ch = this.container.clientHeight || this.canvas.clientHeight;
    if (cw > 50 && ch > 50) {
      this.width = cw;
      this.height = ch;
    } else {
      if (!this.width || this.width <= 50) this.width = 960;
      if (!this.height || this.height <= 50) this.height = 540;
    }

    this.camera3D.aspect = this.width / this.height;
    this.camera3D.updateProjectionMatrix();

    const aspect = this.width / this.height;
    const viewSize = 100;
    this.camera2D.left = -viewSize * aspect;
    this.camera2D.right = viewSize * aspect;
    this.camera2D.top = viewSize;
    this.camera2D.bottom = -viewSize;
    this.camera2D.updateProjectionMatrix();

    this.renderer.setSize(this.width, this.height);
  }

  _animate() {
    requestAnimationFrame(() => this._animate());

    // Slow planetary rotations
    if (this.earthMesh) this.earthMesh.rotation.y += 0.0006;
    if (this.moonMesh) this.moonMesh.rotation.y += 0.0002;

    // Pulse splashdown beacon
    if (this.splashBeacon) {
      const s = 1.0 + 0.3 * Math.sin(Date.now() * 0.005);
      this.splashBeacon.scale.set(s, s, s);
    }

    if (this.controls) this.controls.update();

    this._updateCallouts();
    this.renderer.render(this.scene, this.camera);
  }
}

window.OrionOrbit3D = OrionOrbit3D;
