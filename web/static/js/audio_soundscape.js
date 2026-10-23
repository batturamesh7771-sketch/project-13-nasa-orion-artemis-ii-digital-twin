/**
 * NASA Artemis II Digital Twin — Audio Soundscape & CAPCOM Flight Comm Engine
 *
 * Implements:
 *   1. Authentic NASA Quindar Tones (Intro: 2525 Hz, Outro: 2475 Hz)
 *   2. Physical Spaceflight Acoustic Synthesis via Web Audio API:
 *      - SLS Liftoff Acoustic Rumble & Solid Rocket Motor Roar
 *      - Max-Q Aerodynamic Buffeting & Transonic Pressure Hiss
 *      - Deep Space Orion Cabin ECLSS Avionics Hum (Vacuum Silence)
 *      - Reaction Control System (RCS) Pulse Thruster Bursts
 *      - 5,000°F Hypersonic Reentry Atmospheric Plasma Roar
 *      - Forward Bay Cover & Parachute Mortar Ejection Pops
 *      - Pacific Ocean Splashdown Hydrodynamic Water Plume Thud
 *   3. NASA Air-to-Ground (A/G) Radio Transmissions with Realistic Squelch & Bandpass
 */

class ArtemisAudioEngine {
  constructor() {
    this.audioCtx = null;
    this.isEnabled = false;
    this.masterGain = null;

    // Sound Generator Nodes
    this.rumbleSource = null;
    this.rumbleGain = null;
    this.rumbleFilter = null;

    this.maxQSource = null;
    this.maxQGain = null;

    this.cabinHumOsc = null;
    this.cabinHumGain = null;

    this.reentrySource = null;
    this.reentryGain = null;
    this.reentryFilter = null;

    // Milestone tracking for single-fire CAPCOM calls
    this.lastTriggeredMilestone = -1;
    this.isSpeaking = false;

    // NASA CAPCOM Radio Script
    this.capcomScript = {
      0: { text: "Artemis II, Houston, Tower cleared, roll program initiated.", callsign: "CAPCOM" },
      129: { text: "Artemis II, Houston, solid rocket booster separation confirmed, trajectory nominal.", callsign: "CAPCOM" },
      494: { text: "Artemis II, Houston, core stage MECO and separation nominal. Welcome to orbit.", callsign: "CAPCOM" },
      90840: { text: "Artemis II, Houston, Flight Dynamics reports Go for Trans-Lunar Injection burn.", callsign: "CAPCOM" },
      255600: { text: "Artemis II, Houston, standing by for Loss of Signal behind lunar far side. Perilune 7,400 kilometers.", callsign: "CAPCOM" },
      432000: { text: "Artemis II, Houston, Acquisition of Signal on trans-Earth return coast, systems all green.", callsign: "CAPCOM" },
      575700: { text: "Artemis II, Houston, European Service Module pyrotechnic separation confirmed. Orienting heatshield forward.", callsign: "CAPCOM" },
      576400: { text: "Houston Flight, Orion has reached Entry Interface. Standing by through 5,000 degree plasma blackout.", callsign: "FLIGHT" },
      577200: { text: "Radar contact established! Forward bay cover jettisoned, twin drogue chutes deployed.", callsign: "RECOVERY" },
      577500: { text: "Houston has visual! Three good main canopies spotted descending through 9,500 feet.", callsign: "RECOVERY" },
      578110: { text: "Splashdown confirmed in the Pacific Ocean! Welcome home, Reid, Victor, Christina, and Jeremy!", callsign: "CAPCOM" },
      578160: { text: "Navy RHIB and USS Portland on scene. Five CMUS uprighting bags inflated nominal.", callsign: "RECOVERY" }
    };
  }

  init() {
    if (this.audioCtx) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContextClass();

      this.masterGain = this.audioCtx.createGain();
      this.masterGain.gain.setValueAtTime(0.35, this.audioCtx.currentTime);
      this.masterGain.connect(this.audioCtx.destination);

      this._buildLiftoffRumble();
      this._buildMaxQBuffet();
      this._buildCabinHum();
      this._buildReentryRoar();

      this.isEnabled = true;
      this._updateUIState();
      console.log('[*] Artemis Audio Engine initialized & active.');
    } catch (err) {
      console.warn('AudioContext initialization failed:', err);
    }
  }

  toggle() {
    if (!this.audioCtx) {
      this.init();
      return;
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    this.isEnabled = !this.isEnabled;
    if (this.masterGain) {
      this.masterGain.gain.setTargetAtTime(this.isEnabled ? 0.35 : 0.0, this.audioCtx.currentTime, 0.05);
    }
    this._updateUIState();
  }

  _updateUIState() {
    const btn = document.getElementById('btnToggleAudio');
    if (btn) {
      if (this.isEnabled) {
        btn.innerHTML = '🔊 AUDIO: ON';
        btn.classList.add('active');
        btn.style.borderColor = 'var(--accent-green)';
        btn.style.color = 'var(--accent-green)';
      } else {
        btn.innerHTML = '🔇 AUDIO: OFF';
        btn.classList.remove('active');
        btn.style.borderColor = 'var(--border-subtle)';
        btn.style.color = 'var(--text-muted)';
      }
    }
  }

  // Pink Noise Generator
  _createNoiseBuffer() {
    const bufferSize = this.audioCtx.sampleRate * 2;
    const buffer = this.audioCtx.createBuffer(1, bufferSize, this.audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      b3 = 0.86650 * b3 + white * 0.3104856;
      b4 = 0.55000 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.0168980;
      data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.08;
      b6 = white * 0.115926;
    }
    return buffer;
  }

  // 1. SLS Liftoff Deep Rumble (Sub-Bass + Filtered Noise)
  _buildLiftoffRumble() {
    const noiseBuffer = this._createNoiseBuffer();
    this.rumbleSource = this.audioCtx.createBufferSource();
    this.rumbleSource.buffer = noiseBuffer;
    this.rumbleSource.loop = true;

    this.rumbleFilter = this.audioCtx.createBiquadFilter();
    this.rumbleFilter.type = 'lowpass';
    this.rumbleFilter.frequency.setValueAtTime(110, this.audioCtx.currentTime);

    this.rumbleGain = this.audioCtx.createGain();
    this.rumbleGain.gain.setValueAtTime(0.0, this.audioCtx.currentTime);

    this.rumbleSource.connect(this.rumbleFilter);
    this.rumbleFilter.connect(this.rumbleGain);
    this.rumbleGain.connect(this.masterGain);
    this.rumbleSource.start();
  }

  // 2. Max-Q Buffeting (Bandpass Air Hiss)
  _buildMaxQBuffet() {
    const noiseBuffer = this._createNoiseBuffer();
    this.maxQSource = this.audioCtx.createBufferSource();
    this.maxQSource.buffer = noiseBuffer;
    this.maxQSource.loop = true;

    const bpFilter = this.audioCtx.createBiquadFilter();
    bpFilter.type = 'bandpass';
    bpFilter.frequency.setValueAtTime(320, this.audioCtx.currentTime);
    bpFilter.Q.setValueAtTime(1.8, this.audioCtx.currentTime);

    this.maxQGain = this.audioCtx.createGain();
    this.maxQGain.gain.setValueAtTime(0.0, this.audioCtx.currentTime);

    this.maxQSource.connect(bpFilter);
    bpFilter.connect(this.maxQGain);
    this.maxQGain.connect(this.masterGain);
    this.maxQSource.start();
  }

  // 3. Cabin Avionics & ECLSS Hum (Subtle Twin Sine Oscillators)
  _buildCabinHum() {
    const osc1 = this.audioCtx.createOscillator();
    const osc2 = this.audioCtx.createOscillator();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(60, this.audioCtx.currentTime);
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(120, this.audioCtx.currentTime);

    this.cabinHumGain = this.audioCtx.createGain();
    this.cabinHumGain.gain.setValueAtTime(0.0, this.audioCtx.currentTime);

    osc1.connect(this.cabinHumGain);
    osc2.connect(this.cabinHumGain);
    this.cabinHumGain.connect(this.masterGain);
    osc1.start();
    osc2.start();
  }

  // 4. Reentry Hypersonic Roar
  _buildReentryRoar() {
    const noiseBuffer = this._createNoiseBuffer();
    this.reentrySource = this.audioCtx.createBufferSource();
    this.reentrySource.buffer = noiseBuffer;
    this.reentrySource.loop = true;

    this.reentryFilter = this.audioCtx.createBiquadFilter();
    this.reentryFilter.type = 'bandpass';
    this.reentryFilter.frequency.setValueAtTime(650, this.audioCtx.currentTime);
    this.reentryFilter.Q.setValueAtTime(1.2, this.audioCtx.currentTime);

    this.reentryGain = this.audioCtx.createGain();
    this.reentryGain.gain.setValueAtTime(0.0, this.audioCtx.currentTime);

    this.reentrySource.connect(this.reentryFilter);
    this.reentryFilter.connect(this.reentryGain);
    this.reentryGain.connect(this.masterGain);
    this.reentrySource.start();
  }

  // Play Quindar Tone (Intro: 2525 Hz, Outro: 2475 Hz, Duration: 250 ms)
  playQuindar(isIntro = true) {
    if (!this.audioCtx || !this.isEnabled) return;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(isIntro ? 2525 : 2475, this.audioCtx.currentTime);

    gain.gain.setValueAtTime(0.12, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.25);

    osc.connect(gain);
    gain.connect(this.masterGain);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.25);
  }

  // Play RCS Thruster Burst (80 ms burst)
  playRCSBurst() {
    if (!this.audioCtx || !this.isEnabled) return;
    const noiseBuffer = this._createNoiseBuffer();
    const src = this.audioCtx.createBufferSource();
    src.buffer = noiseBuffer;

    const bp = this.audioCtx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.setValueAtTime(180, this.audioCtx.currentTime);

    const gain = this.audioCtx.createGain();
    gain.gain.setValueAtTime(0.2, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.08);

    src.connect(bp);
    bp.connect(gain);
    gain.connect(this.masterGain);
    src.start();
    src.stop(this.audioCtx.currentTime + 0.08);
  }

  // Play Parachute Mortar Deploy Pop
  playMortarPop() {
    if (!this.audioCtx || !this.isEnabled) return;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(140, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(40, this.audioCtx.currentTime + 0.3);

    gain.gain.setValueAtTime(0.4, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(this.masterGain);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.35);
  }

  // Play Splashdown Water Plume Impact
  playSplashdownImpact() {
    if (!this.audioCtx || !this.isEnabled) return;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(80, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(25, this.audioCtx.currentTime + 1.2);

    gain.gain.setValueAtTime(0.6, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 1.2);

    osc.connect(gain);
    gain.connect(this.masterGain);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 1.2);
  }

  // Speak CAPCOM Transmission with Radio Quindar Framing & Squelch
  speakCapcom(text, callsign = "CAPCOM") {
    if (!this.isEnabled) return;
    if (this.isSpeaking) return;
    if (!('speechSynthesis' in window)) return;

    this.isSpeaking = true;
    this.playQuindar(true);

    // Show radio HUD badge
    const badge = document.getElementById('radioCommsHUD');
    if (badge) {
      badge.style.display = 'flex';
      const txt = document.getElementById('radioCommsText');
      if (txt) txt.textContent = `[${callsign}] "${text}"`;
    }

    setTimeout(() => {
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1.05;
      utter.pitch = 0.95;

      utter.onend = () => {
        this.playQuindar(false);
        this.isSpeaking = false;
        setTimeout(() => {
          if (badge) badge.style.display = 'none';
        }, 1500);
      };
      utter.onerror = () => {
        this.isSpeaking = false;
        if (badge) badge.style.display = 'none';
      };

      window.speechSynthesis.speak(utter);
    }, 280);
  }

  triggerCapcomCall(id, text, callsign = "CAPCOM") {
    this.speakCapcom(text, callsign);
  }

  // Dynamic Acoustic Update Driven by Flight Telemetry at 60 FPS
  updateTelemetryAudio(met, isPlaying) {
    if (!this.audioCtx || !this.isEnabled || !isPlaying) {
      if (this.rumbleGain) this.rumbleGain.gain.setTargetAtTime(0.0, this.audioCtx?.currentTime || 0, 0.05);
      if (this.maxQGain) this.maxQGain.gain.setTargetAtTime(0.0, this.audioCtx?.currentTime || 0, 0.05);
      if (this.cabinHumGain) this.cabinHumGain.gain.setTargetAtTime(0.0, this.audioCtx?.currentTime || 0, 0.05);
      if (this.reentryGain) this.reentryGain.gain.setTargetAtTime(0.0, this.audioCtx?.currentTime || 0, 0.05);
      return;
    }

    const t = this.audioCtx.currentTime;

    // 1. SLS Ascent (MET 0 to 494s)
    if (met < 494.0) {
      const isSolidBurn = met <= 129.0;
      const isCoreBurn = met <= 482.0;

      // Liftoff Rumble
      const rumbleVol = isSolidBurn ? 0.35 : (isCoreBurn ? 0.18 : 0.0);
      this.rumbleGain.gain.setTargetAtTime(rumbleVol, t, 0.1);

      // Max-Q Transonic Hiss (peaks at 71s / 41.5 kPa)
      const qDist = Math.abs(met - 71.0);
      const qVol = qDist < 45.0 ? Math.max(0.0, (1.0 - qDist / 45.0) * 0.28) : 0.0;
      this.maxQGain.gain.setTargetAtTime(qVol, t, 0.1);

      this.cabinHumGain.gain.setTargetAtTime(0.0, t, 0.1);
      this.reentryGain.gain.setTargetAtTime(0.0, t, 0.1);
    }
    // 2. Earth Orbit & Lunar Coast (MET 494s to 575,700s)
    else if (met < 575700.0) {
      this.rumbleGain.gain.setTargetAtTime(0.0, t, 0.1);
      this.maxQGain.gain.setTargetAtTime(0.0, t, 0.1);
      this.reentryGain.gain.setTargetAtTime(0.0, t, 0.1);

      // Deep space cabin ECLSS hum
      this.cabinHumGain.gain.setTargetAtTime(0.08, t, 0.2);
    }
    // 3. Skip Reentry & Splashdown (MET 575,700s+)
    else {
      this.rumbleGain.gain.setTargetAtTime(0.0, t, 0.1);
      this.maxQGain.gain.setTargetAtTime(0.0, t, 0.1);
      this.cabinHumGain.gain.setTargetAtTime(0.0, t, 0.1);

      // Reentry Plasma Roar (576,000 to 577,200s)
      if (met >= 576000.0 && met < 577200.0) {
        const peakU = Math.sin(((met - 576000.0) / 1200.0) * Math.PI);
        const roarVol = Math.max(0.0, peakU * 0.45);
        this.reentryGain.gain.setTargetAtTime(roarVol, t, 0.1);
        this.reentryFilter.frequency.setTargetAtTime(300 + peakU * 750, t, 0.1);
      } else {
        this.reentryGain.gain.setTargetAtTime(0.0, t, 0.1);
      }
    }

    // Trigger Milestone CAPCOM calls
    this._checkMilestoneCapcom(met);
  }

  _checkMilestoneCapcom(met) {
    // Find closest milestone within ±2 seconds
    for (const [targetMetStr, item] of Object.entries(this.capcomScript)) {
      const targetMet = parseFloat(targetMetStr);
      if (Math.abs(met - targetMet) <= 2.5) {
        if (this.lastTriggeredMilestone !== targetMet) {
          this.lastTriggeredMilestone = targetMet;
          this.speakCapcom(item.text, item.callsign);
          if (targetMet === 577200 || targetMet === 577500) {
            this.playMortarPop();
          } else if (targetMet === 578110) {
            this.playSplashdownImpact();
          }
        }
        break;
      }
    }
  }
}

// Global Singleton Instance
window.artemisAudio = new ArtemisAudioEngine();
window.toggleAudioSoundscape = function() {
  if (window.artemisAudio) {
    window.artemisAudio.toggle();
  }
};
