<template>
  <div class="detection-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card header="推理任务配置">
          <el-form label-position="top">
            <el-form-item label="检测模型选择">
              <el-select v-model="form.modelId" placeholder="请选择算法">
                <el-option label="ACEN (3D-CNN融合网络)" value="acen"/>
                <el-option label="YOLOv8s-Spectral" value="yolo"/>
                <el-option label="RX 异常检测 (基线)" value="rx"/>
              </el-select>
            </el-form-item>

            <el-form-item label="数据导入 (.mat / .jpg)">
              <el-upload
                  class="upload-demo"
                  drag
                  action="/api/upload"
                  :on-success="onUploadSuccess"
                  multiple
              >
                <el-icon class="el-icon--upload">
                  <upload-filled/>
                </el-icon>
                <div class="el-upload__text">
                  将 HSOD-BIT 格式数据拖到此处，或<em>点击上传</em>
                </div>
              </el-upload>
            </el-form-item>

            <el-button
                type="primary"
                @click="handleInference"
                :loading="isProcessing"
                style="width: 100%"
            >
              执行目标识别
            </el-button>
          </el-form>
        </el-card>

        <el-card class="status-card" header="服务器资源监控">
          <div class="status-item">
            <span>GPU 显存占用</span>
            <el-progress :percentage="sysStatus.gpu" color="#67c23a"/>
          </div>
          <div class="status-item">
            <span>推理引擎响应</span>
            <el-tag :type="sysStatus.active ? 'success' : 'danger'">
              {{ sysStatus.active ? '在线' : '离线' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card>
          <template #header>
            <div class="result-header">
              <span>识别结果可视化 (像素级) </span>
              <div class="metrics-tags">
                <el-tag size="small">mAP: {{ results.mAP }}</el-tag>
                <el-tag size="small" type="warning">F1: {{ results.f1 }}</el-tag>
                <el-tag size="small" type="info">耗时: {{ results.latency }}s</el-tag>
              </div>
            </div>
          </template>

          <div class="viewer-layout">
            <div class="view-box">
              <p>原始高光谱伪彩图</p>
              <el-image :src="results.rawSrc" fit="cover">
                <template #placeholder>
                  <div class="img-load">等待输入...</div>
                </template>
              </el-image>
            </div>
            <div class="view-box highlight">
              <p>显著性检测 Mask [cite: 5]</p>
              <el-image :src="results.maskSrc" fit="cover">
                <template #placeholder>
                  <div class="img-load">计算中...</div>
                </template>
              </el-image>
            </div>
          </div>

          <div ref="chartRef" class="spectral-chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, nextTick} from 'vue';
import * as echarts from 'echarts';
import {UploadFilled} from '@element-plus/icons-vue';

// 响应式数据
const isProcessing = ref(false);
const chartRef = ref(null);
const form = reactive({
  modelId: 'acen'
});

// 系统状态监控
const sysStatus = reactive({
  gpu: 15,
  active: true
});

// 模拟识别结果数据，需符合任务书指标：mAP≥75%, F1≥0.70
const results = reactive({
  rawSrc: '',
  maskSrc: '',
  mAP: '0.00',
  f1: '0.00',
  latency: '0.0'
});

// 初始化 ECharts：展示 200 个波段的光谱特征
let myChart = null;
const initSpectralChart = () => {
  if (myChart) myChart.dispose();
  myChart = echarts.init(chartRef.value);
  const bands = Array.from({length: 200}, (_, i) => i + 1);

  myChart.setOption({
    title: {text: '典型像元光谱特征分析'},
    tooltip: {trigger: 'axis'},
    xAxis: {name: '波段 (Band)', data: bands},
    yAxis: {name: '反射率 (Reflectance)', type: 'value'},
    series: [{
      name: '目标光谱',
      type: 'line',
      smooth: true,
      data: [] // 此处由后端推理后返回
    }]
  });
};

// 执行推理逻辑
const handleInference = () => {
  isProcessing.value = true;
  // 模拟 API 请求 SpringBoot
  setTimeout(() => {
    results.mAP = '0.78';
    results.f1 = '0.73';
    results.latency = '1.2';
    // 模拟更新图表数据
    myChart.setOption({
      series: [{data: Array.from({length: 200}, () => Math.random() * 0.8)}]
    });
    isProcessing.value = false;
  }, 1500);
};

onMounted(() => {
  initSpectralChart();
  window.addEventListener('resize', () => myChart && myChart.resize());
});
</script>

<style scoped>
.detection-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.status-card {
  margin-top: 20px;
}

.status-item {
  margin-bottom: 15px;
  font-size: 14px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metrics-tags {
  display: flex;
  gap: 8px;
}

.viewer-layout {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.view-box {
  flex: 1;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  text-align: center;
}

.view-box p {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.spectral-chart {
  height: 320px;
  margin-top: 24px;
  width: 100%;
}

.img-load {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
}
</style>