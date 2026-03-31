(function () {
  'use strict';

  // 等待 DOM 加载完成
  function initWhenReady() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initParticles);
    } else {
      // DOM 已经加载完成
      initParticles();
    }
  }

  function initParticles() {
    // 检测是否在首页
    if (!document.querySelector('.hero-section')) {
      return;
    }

    // 检测WebGL支持
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) {
      console.log('WebGL not supported, skipping particle animation');
      return;
    }

    // --- CONFIG (from BreathDearMedusae defaults.js) ---
    const CONFIG = {
      cursor: { radius: 0.065, strength: 3, dragFactor: 0.015 },
      halo: {
        outerOscFrequency: 2.6, outerOscAmplitude: 0.76,
        radiusBase: 2.4, radiusAmplitude: 0.5, shapeAmplitude: 0.75,
        rimWidth: 1.8, outerStartOffset: 0.4, outerEndOffset: 2.2,
        scaleX: 1.3, scaleY: 1
      },
      particles: {
        baseSize: 0.016, activeSize: 0.044,
        blobScaleX: 1, blobScaleY: 0.6,
        rotationSpeed: 0.1, rotationJitter: 0.2,
        cursorFollowStrength: 1, oscillationFactor: 1,
        colorBase: '#0000ff', colorOne: '#4285f5',
        colorTwo: '#eb4236', colorThree: '#faba03'
      },
      background: { color: '#ffffff' }
    };

    // --- VERTEX SHADER (from Medusae.jsx) ---
    const vertexShader = [
      'uniform float uTime;',
      'uniform vec2 uMouse;',
      'uniform float uOuterOscFrequency;',
      'uniform float uOuterOscAmplitude;',
      'uniform float uHaloRadiusBase;',
      'uniform float uHaloRadiusAmplitude;',
      'uniform float uHaloShapeAmplitude;',
      'uniform float uHaloRimWidth;',
      'uniform float uHaloOuterStartOffset;',
      'uniform float uHaloOuterEndOffset;',
      'uniform float uHaloScaleX;',
      'uniform float uHaloScaleY;',
      'uniform float uParticleBaseSize;',
      'uniform float uParticleActiveSize;',
      'uniform float uBlobScaleX;',
      'uniform float uBlobScaleY;',
      'uniform float uParticleRotationSpeed;',
      'uniform float uParticleRotationJitter;',
      'uniform float uParticleOscillationFactor;',
      'varying vec2 vUv;',
      'varying float vSize;',
      'varying vec2 vPos;',
      'attribute vec3 aOffset;',
      'attribute float aRandom;',
      '',
      'float hash(vec2 p) {',
      '  return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);',
      '}',
      'float noise(vec2 p) {',
      '  vec2 i = floor(p);',
      '  vec2 f = fract(p);',
      '  f = f * f * (3.0 - 2.0 * f);',
      '  float a = hash(i);',
      '  float b = hash(i + vec2(1.0, 0.0));',
      '  float c = hash(i + vec2(0.0, 1.0));',
      '  float d = hash(i + vec2(1.0, 1.0));',
      '  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);',
      '}',
      '',
      'void main() {',
      '  vUv = uv;',
      '  vec3 pos = aOffset;',
      '  float driftSpeed = uTime * 0.15;',
      '  float dx = sin(driftSpeed + pos.y * 0.5) + sin(driftSpeed * 0.5 + pos.y * 2.0);',
      '  float dy = cos(driftSpeed + pos.x * 0.5) + cos(driftSpeed * 0.5 + pos.x * 2.0);',
      '  pos.x += dx * 0.25;',
      '  pos.y += dy * 0.25;',
      '',
      '  vec2 relToMouse = pos.xy - uMouse;',
      '  vec2 haloScale = max(vec2(uHaloScaleX, uHaloScaleY), vec2(0.0001));',
      '  float distFromMouse = length(relToMouse / haloScale);',
      '  vec2 dirToMouse = normalize(relToMouse + vec2(0.0001, 0.0));',
      '  float shapeFactor = noise(dirToMouse * 2.0 + vec2(0.0, uTime * 0.1));',
      '  float breathCycle = sin(uTime * 0.8);',
      '  float baseRadius = uHaloRadiusBase + breathCycle * uHaloRadiusAmplitude;',
      '  float currentRadius = baseRadius + (shapeFactor * uHaloShapeAmplitude);',
      '  float dist = distFromMouse;',
      '  float rimInfluence = smoothstep(uHaloRimWidth, 0.0, abs(dist - currentRadius));',
      '  vec2 pushDir = normalize(relToMouse + vec2(0.0001, 0.0));',
      '  float pushAmt = (breathCycle * 0.5 + 0.5) * 0.5;',
      '  pos.xy += pushDir * pushAmt * rimInfluence;',
      '  pos.z += rimInfluence * 0.3 * sin(uTime);',
      '',
      '  float outerInfluence = smoothstep(baseRadius + uHaloOuterStartOffset, baseRadius + uHaloOuterEndOffset, dist);',
      '  float outerOsc = sin(uTime * uOuterOscFrequency + pos.x * 0.6 + pos.y * 0.6);',
      '  pos.xy += normalize(relToMouse + vec2(0.0001, 0.0)) * outerOsc * uOuterOscAmplitude * outerInfluence;',
      '',
      '  float bSize = uParticleBaseSize + (sin(uTime + pos.x) * 0.003);',
      '  float currentScale = bSize + (rimInfluence * uParticleActiveSize);',
      '  float stretch = rimInfluence * 0.02;',
      '  vec3 transformed = position;',
      '  transformed.x *= (currentScale + stretch) * uBlobScaleX;',
      '  transformed.y *= currentScale * uBlobScaleY;',
      '  vSize = rimInfluence;',
      '  vPos = pos.xy;',
      '',
      '  float dirLen = max(length(relToMouse), 0.0001);',
      '  vec2 dir = relToMouse / dirLen;',
      '  float oscPhase = aRandom * 6.28318530718;',
      '  float osc = 0.5 + 0.5 * sin(uTime * (0.25 + uParticleOscillationFactor * 0.35) + oscPhase);',
      '  float speedScale = mix(0.55, 1.35, osc) * (0.8 + uParticleOscillationFactor * 0.2);',
      '  float jitterScale = mix(0.7, 1.45, osc) * (0.85 + uParticleOscillationFactor * 0.15);',
      '  float jitter = sin(uTime * uParticleRotationSpeed * speedScale + pos.x * 0.35 + pos.y * 0.35) * (uParticleRotationJitter * jitterScale);',
      '  vec2 perp = vec2(-dir.y, dir.x);',
      '  vec2 jitteredDir = normalize(dir + perp * jitter);',
      '  mat2 rot = mat2(jitteredDir.x, jitteredDir.y, -jitteredDir.y, jitteredDir.x);',
      '  transformed.xy = rot * transformed.xy;',
      '',
      '  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos + transformed, 1.0);',
      '}'
    ].join('\n');

    // --- FRAGMENT SHADER (from Medusae.jsx) ---
    const fragmentShader = [
      'uniform float uTime;',
      'uniform vec3 uParticleColorBase;',
      'uniform vec3 uParticleColorOne;',
      'uniform vec3 uParticleColorTwo;',
      'uniform vec3 uParticleColorThree;',
      'varying vec2 vUv;',
      'varying float vSize;',
      'varying vec2 vPos;',
      '',
      'void main() {',
      '  vec2 center = vec2(0.5);',
      '  vec2 pos = abs(vUv - center) * 2.0;',
      '  float d = pow(pow(pos.x, 2.6) + pow(pos.y, 2.6), 1.0 / 2.6);',
      '  float alpha = 1.0 - smoothstep(0.8, 1.0, d);',
      '  if (alpha < 0.01) discard;',
      '',
      '  vec3 black = uParticleColorBase;',
      '  vec3 cBlue = uParticleColorOne;',
      '  vec3 cRed = uParticleColorTwo;',
      '  vec3 cYellow = uParticleColorThree;',
      '  float t = uTime * 1.2;',
      '  float p1 = sin(vPos.x * 0.8 + t);',
      '  float p2 = sin(vPos.y * 0.8 + t * 0.8 + p1);',
      '  vec3 activeColor = mix(cBlue, cRed, p1 * 0.5 + 0.5);',
      '  activeColor = mix(activeColor, cYellow, p2 * 0.5 + 0.5);',
      '  vec3 finalColor = mix(black, activeColor, smoothstep(0.1, 0.8, vSize));',
      '  float finalAlpha = alpha * mix(0.4, 0.95, vSize);',
      '  gl_FragColor = vec4(finalColor, finalAlpha);',
      '}'
    ].join('\n');

    // --- THREE.JS SETUP ---
    var scene = new THREE.Scene();
    scene.background = new THREE.Color(CONFIG.background.color);

  var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.z = 4;

    var renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    // 添加canvas到hero-section
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
      renderer.domElement.id = 'hero-canvas';
      heroSection.insertBefore(renderer.domElement, heroSection.firstChild);

      // 设置canvas尺寸为hero-section的尺寸
      const updateCanvasSize = function () {
        const width = heroSection.offsetWidth;
        const height = heroSection.offsetHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      };

      // 初始化尺寸
      updateCanvasSize();

      // 使用ResizeObserver监听hero-section尺寸变化
      const resizeObserver = new ResizeObserver(function () {
        updateCanvasSize();
      });
      resizeObserver.observe(heroSection);
    } else {
      console.error('Hero section not found');
      return;
    }

    // --- INSTANCED MESH ---
    var countX = 100;
    var countY = 55;
    var count = countX * countY;

    var geo = new THREE.PlaneGeometry(1, 1);

    var uniforms = {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uOuterOscFrequency: { value: CONFIG.halo.outerOscFrequency },
      uOuterOscAmplitude: { value: CONFIG.halo.outerOscAmplitude },
      uHaloRadiusBase: { value: CONFIG.halo.radiusBase },
      uHaloRadiusAmplitude: { value: CONFIG.halo.radiusAmplitude },
      uHaloShapeAmplitude: { value: CONFIG.halo.shapeAmplitude },
      uHaloRimWidth: { value: CONFIG.halo.rimWidth },
      uHaloOuterStartOffset: { value: CONFIG.halo.outerStartOffset },
      uHaloOuterEndOffset: { value: CONFIG.halo.outerEndOffset },
      uHaloScaleX: { value: CONFIG.halo.scaleX },
      uHaloScaleY: { value: CONFIG.halo.scaleY },
      uParticleBaseSize: { value: CONFIG.particles.baseSize },
      uParticleActiveSize: { value: CONFIG.particles.activeSize },
      uBlobScaleX: { value: CONFIG.particles.blobScaleX },
      uBlobScaleY: { value: CONFIG.particles.blobScaleY },
      uParticleRotationSpeed: { value: CONFIG.particles.rotationSpeed },
      uParticleRotationJitter: { value: CONFIG.particles.rotationJitter },
      uParticleOscillationFactor: { value: CONFIG.particles.oscillationFactor },
      uParticleColorBase: { value: new THREE.Color(CONFIG.particles.colorBase) },
      uParticleColorOne: { value: new THREE.Color(CONFIG.particles.colorOne) },
      uParticleColorTwo: { value: new THREE.Color(CONFIG.particles.colorTwo) },
      uParticleColorThree: { value: new THREE.Color(CONFIG.particles.colorThree) },
    };

    var mat = new THREE.ShaderMaterial({
      uniforms: uniforms,
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
      transparent: true,
      depthWrite: false
    });

  var offsets = new Float32Array(count * 3);
  var randoms = new Float32Array(count);
  var gridWidth = 40;
  var gridHeight = 22;
  var jitterAmt = 0.25;

    var idx = 0;
    for (var y = 0; y < countY; y++) {
      for (var x = 0; x < countX; x++) {
        var u = x / (countX - 1);
        var v = y / (countY - 1);
        offsets[idx * 3] = (u - 0.5) * gridWidth + (Math.random() - 0.5) * jitterAmt;
        offsets[idx * 3 + 1] = (v - 0.5) * gridHeight + (Math.random() - 0.5) * jitterAmt;
        offsets[idx * 3 + 2] = 0;
        randoms[idx] = Math.random();
        idx++;
      }
    }

    geo.setAttribute('aOffset', new THREE.InstancedBufferAttribute(offsets, 3));
    geo.setAttribute('aRandom', new THREE.InstancedBufferAttribute(randoms, 1));

    var mesh = new THREE.InstancedMesh(geo, mat, count);
    scene.add(mesh);

    // --- MOUSE TRACKING ---
    var hovering = true;
    var mouseTarget = { x: 0, y: 0 };
    var mouseCurrent = new THREE.Vector2(0, 0);

    function getViewportSize() {
      var vFov = (camera.fov * Math.PI) / 180;
      var h = 2 * Math.tan(vFov / 2) * camera.position.z;
      return { width: h * camera.aspect, height: h };
    }

    window.addEventListener('pointermove', function (e) {
      hovering = true;
      var rect = heroSection.getBoundingClientRect();
      var relX = e.clientX - rect.left;
      var relY = e.clientY - rect.top;
      var ndcX = (relX / rect.width) * 2 - 1;
      var ndcY = -(relY / rect.height) * 2 + 1;
      var vp = getViewportSize();
      var t = performance.now() / 1000;
      var jr = Math.min(vp.width, vp.height) * CONFIG.cursor.radius;
      var jx = (Math.sin(t * 0.35) + Math.sin(t * 0.77 + 1.2)) * 0.5;
      var jy = (Math.cos(t * 0.31) + Math.sin(t * 0.63 + 2.4)) * 0.5;
      mouseTarget.x = ((ndcX * vp.width) / 2 + jx * jr * CONFIG.cursor.strength) * CONFIG.particles.cursorFollowStrength;
      mouseTarget.y = ((ndcY * vp.height) / 2 + jy * jr * CONFIG.cursor.strength) * CONFIG.particles.cursorFollowStrength;
    });

    document.body.addEventListener('mouseleave', function () { hovering = false; });
    document.body.addEventListener('mouseenter', function () { hovering = true; });

    window.addEventListener('touchmove', function (e) {
      hovering = true;
      var touch = e.touches[0];
      var rect = heroSection.getBoundingClientRect();
      var relX = touch.clientX - rect.left;
      var relY = touch.clientY - rect.top;
      var vp = getViewportSize();
      mouseTarget.x = ((relX / rect.width) * 2 - 1) * vp.width / 2;
      mouseTarget.y = (-(relY / rect.height) * 2 + 1) * vp.height / 2;
    }, { passive: true });

    // --- THEME SWITCHING ---
    const updateTheme = function () {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const color = isDark ? '#09090b' : '#ffffff';
      CONFIG.background.color = color;
      if (scene && scene.background) {
        scene.background = new THREE.Color(color);
      }
    };

    // Initialize theme
    updateTheme();

    // Watch for theme changes
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.attributeName === 'data-theme') {
          updateTheme();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    // --- ANIMATION ---
    var clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);
      uniforms.uTime.value = clock.getElapsedTime();

      if (hovering) {
        mouseCurrent.x += (mouseTarget.x - mouseCurrent.x) * CONFIG.cursor.dragFactor;
        mouseCurrent.y += (mouseTarget.y - mouseCurrent.y) * CONFIG.cursor.dragFactor;
      }
      uniforms.uMouse.value.copy(mouseCurrent);

      renderer.render(scene, camera);
    }

    animate();
  }

  // 启动初始化
  initWhenReady();
})();
