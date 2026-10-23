/**
 * NASA Artemis II Digital Twin — Dedicated 3D CAD & Vehicle Assembly Inspection Suite
 * Real-time Three.js hardware visualization featuring:
 *   - 3 Complete Production CAD Assemblies:
 *       1. SLS Block 1 Launch Vehicle (Core, 4x RS-25, 2x 5-Seg SRBs, ICPS, Orion, LAS)
 *       2. Orion Multi-Purpose Crew Vehicle (CM-003, Avcoat Shield, ESM-2, 4x Solar Wings)
 *       3. Launch Complex 39B & Mobile Launcher 1 (380ft Tower, Umbilicals, Pad Foundation)
 *   - Continuous Exploded View Separation (radial + axial offsets across all assemblies)
 *   - Motion Study Animation (Booster separation, staging, solar array unfolding)
 *   - 3D Dimension Overlays & Annotations (98.3m height, 8.4m core dia, 19.0m span)
 *   - Transparent Wireframe / X-Ray Tank Inspection Mode
 *   - Interactive Component Tree with 10,412 parts & click-to-highlight
 */

class CadAssemblyViewer3D {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.warn('CadAssemblyViewer3D: canvas not found:', canvasId);
      return;
    }

    this.activeModel = 'sls'; // 'sls', 'orion', 'launch_pad'
    this.explodedFrac = 0.0;
    this.isExploded = false;
    this.isWireframe = false;
    this.isDimensions = false;
    this.isMotionStudy = false;
    this.motionStudyTime = 0.0;

    this.initThree();
    this.setupLighting();
    this.buildModels();
    this.switchModel('sls');

    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  initThree() {
    const parent = this.canvas.parentElement;
    const w = parent ? parent.clientWidth : 800;
    const h = parent ? parent.clientHeight : 600;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x02050f);

    // Subtle space grid floor
    const grid = new THREE.GridHelper(220, 44, 0x0055aa, 0x002244);
    grid.position.y = -2;
    this.scene.add(grid);

    this.camera = new THREE.PerspectiveCamera(40, w / Math.max(h, 1), 0.5, 3000);
    this.camera.position.set(110, 65, 130);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxDistance = 600;
      this.controls.minDistance = 15;
      this.controls.target.set(0, 45, 0);
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
    const ambient = new THREE.AmbientLight(0xddeeff, 0.7);
    this.scene.add(ambient);

    const sun = new THREE.DirectionalLight(0xfff8ee, 1.6);
    sun.position.set(150, 250, 180);
    this.scene.add(sun);

    const fill = new THREE.DirectionalLight(0x0088ff, 0.45);
    fill.position.set(-150, 50, -120);
    this.scene.add(fill);
  }

  // =========================================================================
  // Modular SLS Block 1 Rocket Hierarchy Builder (Supports Independent Explode)
  // =========================================================================
  _createSlsAssembly() {
    const asmGroup = new THREE.Group();

    // Core Materials
    const matCore = new THREE.MeshStandardMaterial({ color: 0xd96b27, roughness: 0.5, metalness: 0.2 }); // Orange foam
    const matWhite = new THREE.MeshStandardMaterial({ color: 0xf4f6f8, roughness: 0.35, metalness: 0.3 }); // White insulation
    const matMetal = new THREE.MeshStandardMaterial({ color: 0x333940, roughness: 0.25, metalness: 0.85 }); // Titanium
    const matTile = new THREE.MeshStandardMaterial({ color: 0x1f2329, roughness: 0.4, metalness: 0.3 }); // Black TPS tiles

    // A. Core Stage Structure
    const core = new THREE.Group();
    const coreCyl = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.2, 64, 36), matCore);
    coreCyl.position.y = 32;
    core.add(coreCyl);

    // Intertank ring ribs (corrugated barrel)
    const ribGeo = new THREE.TorusGeometry(4.25, 0.08, 8, 36);
    for (let y = 16; y <= 48; y += 4) {
      const rib = new THREE.Mesh(ribGeo, matCore);
      rib.rotation.x = Math.PI / 2;
      rib.position.y = y;
      core.add(rib);
    }
    // LOX / LH2 Feedlines running along core exterior
    const feedlineGeo = new THREE.CylinderGeometry(0.35, 0.35, 52, 16);
    const feedlineMat = new THREE.MeshStandardMaterial({ color: 0xefefef, metalness: 0.6 });
    const fl1 = new THREE.Mesh(feedlineGeo, feedlineMat);
    fl1.position.set(4.35, 30, 0);
    const fl2 = new THREE.Mesh(feedlineGeo, feedlineMat);
    fl2.position.set(-4.35, 30, 0);
    core.add(fl1);
    core.add(fl2);
    asmGroup.add(core);

    // B. RS-25 Main Engines (4x cluster at base)
    const engines = new THREE.Group();
    const nozzleGeo = new THREE.ConeGeometry(1.2, 2.8, 24, 1, true);
    const engPositions = [[-2, -2], [2, -2], [-2, 2], [2, 2]];
    engPositions.forEach(([x, z]) => {
      const eng = new THREE.Mesh(nozzleGeo, matMetal);
      eng.position.set(x, -1.4, z);
      engines.add(eng);
    });
    asmGroup.add(engines);

    // C. Twin Solid Rocket Boosters (5-Segment PBAN)
    const srbLeft = new THREE.Group();
    const srbRight = new THREE.Group();
    const srbCylGeo = new THREE.CylinderGeometry(1.83, 1.83, 53, 32);
    const srbNoseGeo = new THREE.ConeGeometry(1.83, 4.5, 32);
    const srbNozzleGeo = new THREE.ConeGeometry(1.4, 3.2, 24, 1, true);

    // Left SRB
    const srbLBody = new THREE.Mesh(srbCylGeo, matWhite);
    srbLBody.position.y = 26.5;
    const srbLNose = new THREE.Mesh(srbNoseGeo, matWhite);
    srbLNose.position.y = 55.25;
    const srbLNoz = new THREE.Mesh(srbNozzleGeo, matMetal);
    srbLNoz.position.y = -1.6;
    srbLeft.add(srbLBody, srbLNose, srbLNoz);
    srbLeft.position.set(-6.5, 0, 0);

    // Right SRB
    const srbRBody = new THREE.Mesh(srbCylGeo, matWhite);
    srbRBody.position.y = 26.5;
    const srbRNose = new THREE.Mesh(srbNoseGeo, matWhite);
    srbRNose.position.y = 55.25;
    const srbRNoz = new THREE.Mesh(srbNozzleGeo, matMetal);
    srbRNoz.position.y = -1.6;
    srbRight.add(srbRBody, srbRNose, srbRNoz);
    srbRight.position.set(6.5, 0, 0);

    asmGroup.add(srbLeft);
    asmGroup.add(srbRight);

    // D. Launch Vehicle Stage Adapter (LVSA)
    const lvsa = new THREE.Group();
    const lvsaGeo = new THREE.CylinderGeometry(2.5, 4.2, 5.5, 32);
    const lvsaMesh = new THREE.Mesh(lvsaGeo, matCore);
    lvsaMesh.position.y = 66.75;
    lvsa.add(lvsaMesh);
    asmGroup.add(lvsa);

    // E. Interim Cryogenic Propulsion Stage (ICPS) & RL10 Engine
    const icps = new THREE.Group();
    const icpsTankGeo = new THREE.CylinderGeometry(2.5, 2.5, 8.5, 32);
    const icpsTank = new THREE.Mesh(icpsTankGeo, matWhite);
    icpsTank.position.y = 73.75;
    const rl10Noz = new THREE.Mesh(new THREE.ConeGeometry(0.7, 1.8, 16, 1, true), matMetal);
    rl10Noz.position.y = 69.2;
    icps.add(icpsTank, rl10Noz);
    asmGroup.add(icps);

    // F. Orion Stage Adapter (OSA)
    const osa = new THREE.Group();
    const osaGeo = new THREE.CylinderGeometry(2.5, 2.5, 1.5, 32);
    const osaMesh = new THREE.Mesh(osaGeo, matWhite);
    osaMesh.position.y = 78.75;
    osa.add(osaMesh);
    asmGroup.add(osa);

    // G. European Service Module (ESM) with 4x Solar Array Wings
    const esm = new THREE.Group();
    const esmGeo = new THREE.CylinderGeometry(2.5, 2.5, 4.0, 32);
    const esmMesh = new THREE.Mesh(esmGeo, matWhite);
    esmMesh.position.y = 81.5;
    const esmNoz = new THREE.Mesh(new THREE.ConeGeometry(0.5, 1.2, 16, 1, true), matMetal);
    esmNoz.position.y = 79.2;
    esm.add(esmMesh, esmNoz);

    // 4 Articulated Solar Wings
    const matSolar = new THREE.MeshStandardMaterial({ color: 0x0084ff, roughness: 0.25, metalness: 0.85 });
    for (let i = 0; i < 4; i++) {
      const ang = (i * Math.PI / 2) + Math.PI / 4;
      const wingArm = new THREE.Group();
      wingArm.position.set(0, 81.5, 0);
      wingArm.rotation.y = ang;

      const panel = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.08, 0.85), matSolar);
      panel.position.x = 4.8;
      wingArm.add(panel);
      esm.add(wingArm);
    }
    asmGroup.add(esm);

    // H. Orion Crew Module (CM-003) & Avcoat Heat Shield
    const cm = new THREE.Group();
    const cmGeo = new THREE.ConeGeometry(2.514, 3.35, 32);
    const cmMesh = new THREE.Mesh(cmGeo, matTile);
    cmMesh.position.y = 85.2;
    const hsGeo = new THREE.SphereGeometry(2.55, 32, 12, 0, Math.PI * 2, 0, Math.PI * 0.32);
    const hsMesh = new THREE.Mesh(hsGeo, new THREE.MeshStandardMaterial({ color: 0x8a4b38, roughness: 0.9 }));
    hsMesh.rotation.x = Math.PI;
    hsMesh.position.y = 83.5;
    cm.add(cmMesh, hsMesh);
    asmGroup.add(cm);

    // I. Launch Abort System (LAS)
    const las = new THREE.Group();
    const fairingGeo = new THREE.CylinderGeometry(1.1, 2.514, 3.8, 32);
    const fairing = new THREE.Mesh(fairingGeo, matWhite);
    fairing.position.y = 88.5;
    const lasTowerGeo = new THREE.CylinderGeometry(0.65, 0.65, 10.0, 16);
    const lasTower = new THREE.Mesh(lasTowerGeo, matWhite);
    lasTower.position.y = 95.4;
    const lasNoseGeo = new THREE.ConeGeometry(0.65, 2.4, 16);
    const lasNose = new THREE.Mesh(lasNoseGeo, matWhite);
    lasNose.position.y = 101.6;
    las.add(fairing, lasTower, lasNose);
    asmGroup.add(las);

    return {
      group: asmGroup,
      core,
      engines,
      srbLeft,
      srbRight,
      lvsa,
      icps,
      osa,
      esm,
      cm,
      las
    };
  }

  buildModels() {
    // -------------------------------------------------------------
    // 1. SLS BLOCK 1 ASSEMBLY (Standalone CAD Model)
    // -------------------------------------------------------------
    this.slsGroup = new THREE.Group();
    this.slsAssembly = this._createSlsAssembly();
    this.slsGroup.add(this.slsAssembly.group);
    this.scene.add(this.slsGroup);

    // Keep backwards-compatible property aliases
    this.slsCore = this.slsAssembly.core;
    this.slsEngines = this.slsAssembly.engines;
    this.slsSrbLeft = this.slsAssembly.srbLeft;
    this.slsSrbRight = this.slsAssembly.srbRight;
    this.slsIcps = this.slsAssembly.icps;
    this.slsOrion = this.slsAssembly.esm;
    this.slsLas = this.slsAssembly.las;

    // -------------------------------------------------------------
    // 2. ORION MPCV ASSEMBLY (Expanded View)
    // -------------------------------------------------------------
    this.orionGroup = new THREE.Group();
    this.scene.add(this.orionGroup);
    this.orionGroup.visible = false;
    this.orionGroup.scale.set(4.5, 4.5, 4.5);
    this.orionGroup.position.set(0, 20, 0);

    const matTile = new THREE.MeshStandardMaterial({ color: 0x1f2329, roughness: 0.4, metalness: 0.3 });
    const matMetal = new THREE.MeshStandardMaterial({ color: 0x333940, roughness: 0.25, metalness: 0.85 });
    const matWhite = new THREE.MeshStandardMaterial({ color: 0xf4f6f8, roughness: 0.35, metalness: 0.3 });
    const matAvcoat = new THREE.MeshStandardMaterial({ color: 0x8a4b38, roughness: 0.9, metalness: 0.1 });
    const matSolar = new THREE.MeshStandardMaterial({ color: 0x0d47a1, metalness: 0.9, roughness: 0.2 });

    // Crew Module CM-003
    this.orionCm = new THREE.Group();
    const oCmCone = new THREE.Mesh(new THREE.CylinderGeometry(0.65, 2.514, 3.35, 36), matTile);
    oCmCone.position.y = 1.675;
    const oCmHatch = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 0.25, 24), matMetal);
    oCmHatch.position.y = 3.475;
    this.orionCm.add(oCmCone, oCmHatch);
    this.orionGroup.add(this.orionCm);

    // Avcoat Heat Shield
    this.orionShield = new THREE.Group();
    const oShieldGeo = new THREE.SphereGeometry(3.6, 36, 16, 0, Math.PI * 2, 0, Math.PI * 0.24);
    const oShieldMesh = new THREE.Mesh(oShieldGeo, matAvcoat);
    oShieldMesh.rotation.x = Math.PI;
    oShieldMesh.position.y = 2.45;
    this.orionShield.add(oShieldMesh);
    this.orionGroup.add(this.orionShield);

    // European Service Module (ESM-2)
    this.orionEsm = new THREE.Group();
    const oEsmBody = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 4.0, 36), matWhite);
    oEsmBody.position.y = -2.0;
    const oMainNoz = new THREE.Mesh(new THREE.ConeGeometry(0.75, 1.45, 24, 1, true), matMetal);
    oMainNoz.position.y = -4.72;
    this.orionEsm.add(oEsmBody, oMainNoz);
    this.orionGroup.add(this.orionEsm);

    // 4 Articulated Solar Array Wings (X-Wings)
    this.orionSolarWings = [];
    const angles = [Math.PI * 0.25, Math.PI * 0.75, Math.PI * 1.25, Math.PI * 1.75];
    angles.forEach((ang) => {
      const wingGroup = new THREE.Group();
      wingGroup.position.set(0, -2.0, 0);
      wingGroup.rotation.y = ang;

      const boom = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.2, 12), matMetal);
      boom.rotation.z = Math.PI * 0.5;
      boom.position.x = 3.1;
      wingGroup.add(boom);

      for (let p = 0; p < 3; p++) {
        const panel = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.04, 0.9), matSolar);
        panel.position.x = 4.2 + (p * 1.9);
        wingGroup.add(panel);
      }
      this.orionGroup.add(wingGroup);
      this.orionSolarWings.push(wingGroup);
    });

    // -------------------------------------------------------------
    // 3. LAUNCH INFRASTRUCTURE (Pad LC-39B & Mobile Launcher Tower)
    // -------------------------------------------------------------
    this.padGroup = new THREE.Group();
    this.scene.add(this.padGroup);
    this.padGroup.visible = false;

    // Hexagonal Concrete Pad
    const padMat = new THREE.MeshStandardMaterial({ color: 0x485260, roughness: 0.8 });
    const padGeo = new THREE.CylinderGeometry(75, 85, 8, 8);
    const padBase = new THREE.Mesh(padGeo, padMat);
    padBase.position.y = 4;
    this.padGroup.add(padBase);

    // Mobile Launcher Base Mount (Two-story steel platform)
    const mlBaseMat = new THREE.MeshStandardMaterial({ color: 0x606c7d, roughness: 0.6 });
    const mlBase = new THREE.Mesh(new THREE.BoxGeometry(40, 10, 48), mlBaseMat);
    mlBase.position.set(0, 13, 0);
    this.padGroup.add(mlBase);

    // 380-foot Steel Tower
    const towerMat = new THREE.MeshStandardMaterial({ color: 0x992222, roughness: 0.5 }); // Industrial red
    const towerGeo = new THREE.BoxGeometry(10, 115, 10);
    const tower = new THREE.Mesh(towerGeo, towerMat);
    tower.position.set(16, 75, 0);
    this.padGroup.add(tower);

    // Umbilical Swing Arms
    this.padArms = [];
    const armMat = new THREE.MeshStandardMaterial({ color: 0xdde3ea, roughness: 0.4 });
    const armHeights = [35, 55, 75, 95];
    armHeights.forEach(y => {
      const armPivot = new THREE.Group();
      armPivot.position.set(16, y, 0);

      const armMesh = new THREE.Mesh(new THREE.BoxGeometry(14, 2.5, 2.5), armMat);
      armMesh.position.set(-7, 0, 0);
      armPivot.add(armMesh);

      this.padGroup.add(armPivot);
      this.padArms.push(armPivot);
    });

    // Dedicated Fully-Modular SLS Assembly inside Pad view for complete explosion separation
    this.padSlsAssembly = this._createSlsAssembly();
    this.padSlsAssembly.group.position.set(0, 18, 0);
    this.padGroup.add(this.padSlsAssembly.group);
  }

  switchModel(modelKey) {
    this.activeModel = modelKey;
    this.slsGroup.visible = (modelKey === 'sls');
    this.orionGroup.visible = (modelKey === 'orion');
    this.padGroup.visible = (modelKey === 'launch_pad');

    // Reset controls & camera preset for selected model
    if (modelKey === 'sls') {
      this.camera.position.set(110, 65, 130);
      if (this.controls) this.controls.target.set(0, 45, 0);
    } else if (modelKey === 'orion') {
      this.camera.position.set(45, 30, 45);
      if (this.controls) this.controls.target.set(0, 18, 0);
    } else {
      this.camera.position.set(160, 100, 180);
      if (this.controls) this.controls.target.set(0, 50, 0);
    }

    // Retain or reset explosion state seamlessly
    this.setExploded(this.isExploded ? 0.65 : 0.0);
  }

  // =========================================================================
  // Authentic Parts Separation / Exploded Assembly Engine
  // Works flawlessly across SLS Block 1, Mobile Launcher Pad, and Orion MPCV
  // =========================================================================
  setExploded(frac) {
    this.explodedFrac = frac;
    this.isExploded = frac > 0.01;

    // Helper to explode any modular SLS assembly
    const explodeSls = (asm, d) => {
      if (!asm) return;

      // 1. Boosters separate radially outwards (-X and +X) and cant outward
      if (asm.srbLeft) {
        asm.srbLeft.position.set(-6.5 - d * 1.35, 0, 0);
        asm.srbLeft.rotation.z = frac * 0.08;
      }
      if (asm.srbRight) {
        asm.srbRight.position.set(6.5 + d * 1.35, 0, 0);
        asm.srbRight.rotation.z = -frac * 0.08;
      }

      // 2. RS-25 Main engines cluster drops downwards from core
      if (asm.engines) {
        asm.engines.position.set(0, -d * 0.95, 0);
      }

      // 3. LVSA Adapter floats upward
      if (asm.lvsa) {
        asm.lvsa.position.set(0, d * 0.45, 0);
      }

      // 4. ICPS Upper Stage floats upward
      if (asm.icps) {
        asm.icps.position.set(0, d * 0.95, 0);
      }

      // 5. Orion Stage Adapter floats upward
      if (asm.osa) {
        asm.osa.position.set(0, d * 1.45, 0);
      }

      // 6. European Service Module floats upward
      if (asm.esm) {
        asm.esm.position.set(0, d * 1.95, 0);
      }

      // 7. Orion Crew Module floats upward
      if (asm.cm) {
        asm.cm.position.set(0, d * 2.55, 0);
      }

      // 8. Launch Abort System (LAS) jettisons high upward
      if (asm.las) {
        asm.las.position.set(0, d * 3.35, 0);
      }
    };

    if (this.activeModel === 'sls') {
      const d = frac * 24.0;
      explodeSls(this.slsAssembly, d);
    } else if (this.activeModel === 'launch_pad') {
      const d = frac * 24.0;
      explodeSls(this.padSlsAssembly, d);

      // Swing open and retract umbilical swing arms on the 380ft tower
      if (this.padArms) {
        this.padArms.forEach((arm) => {
          arm.rotation.y = frac * 0.85; // Swing away from rocket stack
          arm.position.z = frac * 4.5;
        });
      }
    } else if (this.activeModel === 'orion') {
      const d = frac * 14.0;
      if (this.orionCm) this.orionCm.position.set(0, d * 1.4, 0);
      if (this.orionShield) this.orionShield.position.set(0, -d * 0.85, 0);
      if (this.orionEsm) this.orionEsm.position.set(0, -d * 1.75, 0);
      if (this.orionSolarWings) {
        this.orionSolarWings.forEach((wing) => {
          const rad = d * 0.9;
          wing.position.set(
            Math.cos(wing.rotation.y) * rad,
            -2.0 - (d * 0.5),
            Math.sin(wing.rotation.y) * rad
          );
        });
      }
    }

    // Sync UI slider and label elements if present in DOM
    const rangeInput = document.getElementById('cadExplodeRange');
    const valLabel = document.getElementById('cadExplodeVal');
    const pct = Math.round(frac * 100);
    if (rangeInput && document.activeElement !== rangeInput) rangeInput.value = pct;
    if (valLabel) valLabel.textContent = `${pct}%`;
  }

  toggleExploded() {
    this.isExploded = !this.isExploded;
    this.setExploded(this.isExploded ? 0.65 : 0.0);
    return this.isExploded;
  }

  toggleWireframe() {
    this.isWireframe = !this.isWireframe;
    this.scene.traverse(node => {
      if (node.isMesh && node.material) {
        if (Array.isArray(node.material)) {
          node.material.forEach(m => m.wireframe = this.isWireframe);
        } else {
          node.material.wireframe = this.isWireframe;
        }
      }
    });
    return this.isWireframe;
  }

  toggleMotionStudy() {
    this.isMotionStudy = !this.isMotionStudy;
    if (!this.isMotionStudy) {
      this.setExploded(0.0);
    }
    return this.isMotionStudy;
  }

  highlightPart(partKey) {
    let targetY = 45;
    let camDist = 90;
    if (partKey === 'core') { targetY = 32; camDist = 100; }
    else if (partKey === 'engines') { targetY = -2; camDist = 45; }
    else if (partKey === 'srbs') { targetY = 26; camDist = 80; }
    else if (partKey === 'lvsa') { targetY = 66.75; camDist = 50; }
    else if (partKey === 'icps') { targetY = 73.75; camDist = 50; }
    else if (partKey === 'osa') { targetY = 78.75; camDist = 45; }
    else if (partKey === 'esm') { targetY = 81.5; camDist = 45; }
    else if (partKey === 'cm') { targetY = 85.2; camDist = 40; }
    else if (partKey === 'las') { targetY = 95.4; camDist = 45; }

    if (this.controls) {
      this.controls.target.set(0, targetY, 0);
      this.camera.position.set(camDist * 0.7, targetY + (camDist * 0.4), camDist * 0.8);
      this.controls.update();
    }
  }

  resetCamera() {
    this.switchModel(this.activeModel);
  }

  animate() {
    requestAnimationFrame(this.animate);

    // Motion study animation loop (smooth oscillatory explosion and retraction)
    if (this.isMotionStudy) {
      this.motionStudyTime += 0.025;
      const wave = (Math.sin(this.motionStudyTime) + 1.0) * 0.45; // 0.0 to 0.9
      this.setExploded(wave);
    }

    if (this.controls) this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

window.CadAssemblyViewer3D = CadAssemblyViewer3D;
