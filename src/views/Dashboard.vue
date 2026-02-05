<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="item in stats" :key="item.title">
        <el-card shadow="hover" class="stat-card">
          <el-statistic :title="item.title" :value="item.value" :precision="item.precision">
            <template #suffix>
              <span :style="{ color: item.color }">{{ item.suffix }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card header="算法性能指标分析 (mAP@0.5 & F1)">
          <div ref="perfChart" style="height: 350px;"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card header="计算节点资源实时负载">
          <el-row :gutter="10">
            <el-col :span="12">
              <div class="monitor-item">
                <el-progress type="dashboard" :percentage="resources.gpuUsage" color="#67c23a">
                  <template #default>
                    <span class="p-value">{{ resources.gpuUsage }}%</span>
                    <span class="p-label">GPU 负载</span>
                  </template>
                </el-progress>
                <p class="res-info">显存占用: {{ resources.vram }} / 12GB</p>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="monitor-item">
                <el-progress type="dashboard" :percentage="resources.ramUsage" color="#409EFF">
                  <template #default>
                    <span class="p-value">{{ resources.ramUsage }}%</span>
                    <span class="p-label">系统内存</span>
                  </template>
                </el-progress>
                <p class="res-info">内存占用: {{ resources.ram }} / 32GB</p>
              </div>
            </el-col>
          </el-row>
          <el-divider content-position="left">存储与 IO 状态</el-divider>
          <div class="disk-status">
            <div class="disk-info">
              <span>HDF5 数据存储 (SSD)</span>
              <el-progress :percentage="82" status="warning"/>
            </div>
            <div class="disk-info">
              <span>系统响应延时 (Redis Cache)</span>
              <el-tag size="small" type="success">{{ resources.latency }}ms</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row class="mt-20">
      <el-col :span="24">
        <el-card header="高光谱数据推理任务队列">
          <el-table :data="taskQueue" stripe size="small">
            <el-table-column prop="id" label="任务ID" width="150"/>
            <el-table-column prop="name" label="数据源 (.mat)"/>
            <el-table-column prop="progress" label="推理进度">
              <template #default="scope">
                <el-progress :percentage="scope.row.progress"/>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === '完成' ? 'success' : 'primary'">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, onMounted, reactive} from 'vue';
import * as echarts from 'echarts';

// 核心业务指标 (基于任务书要求)
const stats = [
  {title: 'HSOD-BIT 数据集立方体', value: 319, suffix: 'Cubes', color: '#409EFF'},
  {title: 'ACEN 验证集 mAP@0.5', value: 78.5, precision: 1, suffix: '%', color: '#67C23A'},
  {title: 'F1-Score 目标识别率', value: 0.72, precision: 2, suffix: '', color: '#E6A23C'},
  {title: '单幅平均响应时间', value: 2.8, precision: 1, suffix: 's', color: '#F56C6C'}
];

// 服务器资源实时数据
const resources = reactive({
  gpuUsage: 45,
  vram: '5.4GB',
  ramUsage: 32,
  ram: '10.2GB',
  latency: 12
});

// 模拟任务队列
const taskQueue = [
  {id: 'T2026020501', name: 'lake_scene_001.mat', progress: 100, status: '完成'},
  {id: 'T2026020502', name: 'industrial_bg_04.mat', progress: 45, status: '推理中'},
  {id: 'T2026020503', name: 'urban_exposure_12.mat', progress: 0, status: '排队中'}
];

const perfChart = ref(null);

onMounted(() => {
  const myChart = echarts.init(perfChart.value);
  myChart.setOption({
    tooltip: {trigger: 'axis'},
    legend: {data: ['mAP@0.5', '推理延迟(s)']},
    xAxis: {type: 'category', data: ['RX (基线)', '3D-CNN', 'ACEN (蒸馏)', 'YOLOv8s-Spe']},
    yAxis: [
      {type: 'value', name: '精度', max: 1},
      {type: 'value', name: '延迟', axisLabel: {formatter: '{value} s'}}
    ],
    series: [
      {name: 'mAP@0.5', type: 'bar', data: [0.55, 0.72, 0.79, 0.76], color: '#67C23A'},
      {name: '推理延迟(s)', type: 'line', yAxisIndex: 1, data: [0.5, 4.2, 2.8, 1.2], color: '#F56C6C'}
    ]
  });

  // 模拟资源动态变化
  setInterval(() => {
    resources.gpuUsage = Math.floor(Math.random() * 20) + 40;
    resources.latency = Math.floor(Math.random() * 5) + 10;
  }, 3000);
});
</script>

<style scoped>
.dashboard {
  padding: 20px;
  background-color: #f5f7fa;
}

.mt-20 {
  margin-top: 20px;
}

.monitor-item {
  text-align: center;
}

.p-value {
  display: block;
  font-size: 20px;
  font-weight: bold;
}

.p-label {
  font-size: 12px;
  color: #909399;
}

.res-info {
  font-size: 13px;
  color: #606266;
  margin-top: 5px;
}

.disk-status {
  padding: 10px;
}

.disk-info {
  margin-bottom: 10px;
  font-size: 14px;
}
</style>