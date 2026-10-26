import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class WeaponViewer {
  constructor(container) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.5;
    this.renderer.domElement.setAttribute('aria-label', 'Modelo 3D del arma. Arrastra para girar y usa la rueda para acercar.');
    this.renderer.domElement.setAttribute('role', 'img');
    container.prepend(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.enablePan = false;
    this.controls.autoRotate = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.controls.autoRotateSpeed = 0.65;
    this.controls.minDistance = 4;
    this.controls.maxDistance = 14;
    this.controls.minPolarAngle = 0.2;
    this.controls.maxPolarAngle = Math.PI * 0.78;
    this.reset();
    this.loader = new GLTFLoader();
    this.requestId = 0;
    this.wireframe = false;
    this.disposed = false;

    this.scene.add(new THREE.HemisphereLight(0xf0f3e9, 0x495347, 3.2));
    const key = new THREE.DirectionalLight(0xfff8e8, 3.7);
    key.position.set(2, 6, 5);
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0xd1ff9e, 3);
    rim.position.set(-4, 2, -3);
    this.scene.add(rim);
    const fill = new THREE.DirectionalLight(0xd7e3fa, 1.8);
    fill.position.set(-4, 1, 4);
    this.scene.add(fill);

    const pedestal = new THREE.Mesh(
      new THREE.CylinderGeometry(2.25, 2.35, 0.22, 96),
      new THREE.MeshStandardMaterial({ color: 0x12190e, roughness: 0.8, metalness: 0.25 }),
    );
    pedestal.position.y = -1.13;
    this.scene.add(pedestal);
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(2.25, 0.012, 8, 96),
      new THREE.MeshBasicMaterial({ color: 0xd4f98a }),
    );
    ring.rotation.x = Math.PI / 2;
    ring.position.y = -1.015;
    this.scene.add(ring);
    const inner = new THREE.Mesh(
      new THREE.RingGeometry(1.92, 1.925, 96),
      new THREE.MeshBasicMaterial({ color: 0x47543b, side: THREE.DoubleSide }),
    );
    inner.rotation.x = -Math.PI / 2;
    inner.position.y = -1.012;
    this.scene.add(inner);

    const shadowCanvas = document.createElement('canvas');
    shadowCanvas.width = shadowCanvas.height = 128;
    const context = shadowCanvas.getContext('2d');
    const gradient = context.createRadialGradient(64, 64, 0, 64, 64, 64);
    gradient.addColorStop(0, 'rgba(0,0,0,0.55)');
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    context.fillStyle = gradient;
    context.fillRect(0, 0, 128, 128);
    const shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(3.6, 2),
      new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(shadowCanvas), transparent: true, depthWrite: false }),
    );
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = -1.005;
    this.scene.add(shadow);

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
    this.previousTime = 0;
    this.renderer.setAnimationLoop((time) => {
      const delta = this.previousTime ? Math.min((time - this.previousTime) / 1000, 0.1) : 0;
      this.previousTime = time;
      this.controls.update(delta);
      this.renderer.render(this.scene, this.camera);
    });
  }

  resize() {
    const { width, height } = this.container.getBoundingClientRect();
    if (!width || !height) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.controls.minDistance = this.camera.aspect < 1 ? 6 : 4;
    if (this.camera.position.length() < this.controls.minDistance) this.reset();
  }

  reset() {
    const narrow = this.container.clientWidth < 500;
    this.camera.position.set(narrow ? 4.2 : 3.3, narrow ? 3 : 2.6, narrow ? 7.4 : 6.2);
    this.controls.target.set(0, -0.15, 0);
    this.controls.update();
  }

  async load(url) {
    const requestId = ++this.requestId;
    const gltf = await this.loader.loadAsync(url);
    if (this.disposed || requestId !== this.requestId) {
      this.disposeObject(gltf.scene);
      return false;
    }
    const model = gltf.scene;
    // The extracted weapon meshes use their local Y axis along the barrel.
    model.rotation.set(-Math.PI / 2, 0, -Math.PI / 2);
    model.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(model);
    const size = bounds.getSize(new THREE.Vector3());
    const scale = 4.3 / Math.max(size.x, size.y, size.z);
    model.scale.setScalar(scale);
    model.updateMatrixWorld(true);
    bounds.setFromObject(model);
    model.position.sub(bounds.getCenter(new THREE.Vector3()));
    model.position.y += 0.25;
    model.traverse((object) => {
      if (!object.isMesh) return;
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) {
        material.wireframe = this.wireframe;
        if (material.map) {
          material.map.magFilter = THREE.NearestFilter;
          material.map.minFilter = THREE.NearestFilter;
        }
      }
    });
    if (this.model) {
      this.scene.remove(this.model);
      this.disposeObject(this.model);
    }
    this.model = model;
    this.scene.add(model);
    this.reset();
    return true;
  }

  setWireframe(enabled) {
    this.wireframe = enabled;
    this.model?.traverse((object) => {
      if (!object.isMesh) return;
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        material.wireframe = enabled;
      }
    });
  }

  disposeObject(object) {
    const geometries = new Set();
    const materials = new Set();
    const textures = new Set();
    object.traverse((child) => {
      if (!child.isMesh) return;
      geometries.add(child.geometry);
      for (const material of Array.isArray(child.material) ? child.material : [child.material]) {
        materials.add(material);
        for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
      }
    });
    for (const texture of textures) texture.dispose();
    for (const material of materials) material.dispose();
    for (const geometry of geometries) geometry.dispose();
  }

  dispose() {
    this.disposed = true;
    ++this.requestId;
    this.resizeObserver.disconnect();
    this.renderer.setAnimationLoop(null);
    this.controls.dispose();
    this.disposeObject(this.scene);
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
