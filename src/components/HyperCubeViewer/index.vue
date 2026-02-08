<template>
  <div class="cube-container" ref="containerRef">
    <div v-if="loading" class="loading-mask">
      <div class="loading-content">
        <el-icon class="is-loading" :size="24">
          <Loading/>
        </el-icon>
        <div class="loading-text">3D 点云加载中...</div>
      </div>
    </div>
    <div class="controls">
      <div class="info">
        <span class="axis-label x-axis">X: 空间维 (W)</span>
        <span class="axis-label z-axis">Z: 空间维 (H)</span>
        <span class="axis-label y-axis">Y: 光谱维 (Bands)</span>
      </div>
      <el-button size="small" @click="resetCamera">重置视角</el-button>
      <el-button size="small" type="primary" @click="toggleRotate">{{
          autoRotate ? '停止旋转' : '自动旋转'
        }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onBeforeUnmount, watch} from 'vue';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls';
import {Loading} from '@element-plus/icons-vue';
import {cubeView} from "@/api/report.js"

const props = defineProps({
  mat: Object
});

const containerRef = ref(null);
const loading = ref(false);
const autoRotate = ref(true);

// Three.js 变量
let scene, camera, renderer, controls, pointsMesh, boxHelper;
let animationId;
// 新增：ResizeObserver 实例变量
let resizeObserver;

// 初始化场景
const initThree = () => {
  if (!containerRef.value) return;

  // 初始获取宽高 (即使是 0 也没关系，Observer 马上会修正)
  const width = containerRef.value.clientWidth || 1;
  const height = containerRef.value.clientHeight || 1;

  // 1. 场景
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x050505);
  scene.fog = new THREE.Fog(0x050505, 200, 2000);

  // 2. 相机
  camera = new THREE.PerspectiveCamera(45, width / height, 1, 5000);
  camera.position.set(400, 400, 400);

  // 3. 渲染器
  renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(width, height);
  containerRef.value.appendChild(renderer.domElement);

  // 4. 控制器
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 2.0;

  // 5. 辅助对象
  const axesHelper = new THREE.AxesHelper(100);
  scene.add(axesHelper);

  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const edges = new THREE.EdgesGeometry(geometry);
  boxHelper = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({color: 0x444444}));
  scene.add(boxHelper);

  // --- 核心修改：添加 ResizeObserver 监听 ---
  resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      // 获取容器最新的内容矩形尺寸
      const {width, height} = entry.contentRect;

      // 只有当尺寸有效且渲染器已初始化时才更新
      if (width > 0 && height > 0 && renderer && camera) {
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
      }
    }
  });
  // 开始监听容器
  resizeObserver.observe(containerRef.value);
  // ---------------------------------------

  animate();
};

// 加载数据逻辑 (保持不变)
const loadData = async () => {
  if (!props.mat) return;
  loading.value = true;

  try {
    const res = await cubeView(props.mat);

    if (res.code === 200) {
      const payload = res.data.data || res.data;
      const {x, y, z, v, bounds} = payload;

      if (!x || !bounds) {
        console.warn("数据格式不完整");
        return;
      }

      const [W, H, B] = bounds;
      boxHelper.scale.set(W, B * 2, H);

      if (pointsMesh) {
        scene.remove(pointsMesh);
        pointsMesh.geometry.dispose();
        pointsMesh.material.dispose();
      }

      const geometry = new THREE.BufferGeometry();
      const positions = [];
      const colors = [];
      const colorObj = new THREE.Color();
      const count = x.length;

      for (let i = 0; i < count; i++) {
        const px = x[i] - W / 2;
        const pz = y[i] - H / 2;
        const py = z[i] * 2 - B;

        positions.push(px, py, pz);

        const val = v[i];
        const hue = (1.0 - val) * 0.7;
        colorObj.setHSL(hue, 1.0, 0.5);
        colors.push(colorObj.r, colorObj.g, colorObj.b);
      }

      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      geometry.computeBoundingSphere();

      const material = new THREE.PointsMaterial({
        size: 2,
        vertexColors: true,
        transparent: true,
        opacity: 0.85,
        sizeAttenuation: true
      });

      pointsMesh = new THREE.Points(geometry, material);
      scene.add(pointsMesh);
    } else {
      console.error(res.msg);
    }

  } catch (err) {
    console.error("加载3D数据失败", err);
  } finally {
    loading.value = false;
  }
};

const animate = () => {
  animationId = requestAnimationFrame(animate);
  if (controls && autoRotate.value) {
    controls.update();
  }
  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
};

const resetCamera = () => {
  camera.position.set(400, 400, 400);
  camera.lookAt(0, 0, 0);
  controls.reset();
};

const toggleRotate = () => {
  autoRotate.value = !autoRotate.value;
};

watch(() => props.mat, (val) => {
  if (val) loadData();
});

onMounted(() => {
  initThree();
  if (props.mat) loadData();
  // 注意：删除了 window.addEventListener，完全交给 ResizeObserver
});

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId);

  // 清理 Observer
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }

  if (renderer) renderer.dispose();
  if (scene) scene.clear();
});
</script>

<style scoped>
/* 样式保持不变 */
.cube-container {
  width: 100%;
  height: 500px;
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.controls {
  position: absolute;
  bottom: 15px;
  left: 15px;
  background: rgba(0, 0, 0, 0.6);
  padding: 10px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  backdrop-filter: blur(4px);
}

.info {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #fff;
  margin-bottom: 5px;
}

.axis-label {
  display: flex;
  align-items: center;
}

.axis-label::before {
  content: '●';
  margin-right: 5px;
  font-size: 14px;
}

.x-axis::before {
  color: #ff0000;
}

.y-axis::before {
  color: #00ff00;
}

.z-axis::before {
  color: #0000ff;
}

.loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  color: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-content {
  text-align: center;
}

.loading-text {
  margin-top: 10px;
  font-size: 14px;
  letter-spacing: 1px;
}
</style>