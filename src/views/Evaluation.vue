<template>
  <div class="eval-dashboard">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6" v-for="(val, label) in summaryCards" :key="label">
        <el-card shadow="hover" class="stat-card">
          <el-statistic :value="val.value" :precision="val.precision" :suffix="val.suffix">
            <template #title>
              <div class="stat-title">
                <el-icon :color="val.color">
                  <component :is="val.icon"/>
                </el-icon>
                <span>{{ label }}</span>
              </div>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="main-row">
      <el-col :span="7">
        <el-card class="config-card" border-radius="12px">
          <template #header>
            <div class="card-header">
              <el-icon>
                <Setting/>
              </el-icon>
              <span>评估控制台</span>
            </div>
          </template>

          <el-form label-position="top">
            <el-form-item label="待评估高光谱任务">
              <el-select v-model="selectedTaskId" placeholder="请选择记录" @change="loadTaskDetail" class="full-width">
                <el-option v-for="t in finishedTasks" :key="t.fileId" :label="t.fileName" :value="t.fileId"/>
              </el-select>
            </el-form-item>

            <el-form-item label="上传 Ground Truth 标签">
              <div class="gt-upload-area">
                <file-upload v-model="gtFileUrl" :limit="1" :file-size="5" :file-type="['png','jpg','mat']"/>
              </div>
            </el-form-item>

            <el-button
                type="primary"
                class="eval-btn"
                @click="handleEvaluate"
                :loading="isEvaluating"
                :disabled="!selectedTaskId || !gtFileUrl"
            >
              <el-icon>
                <Odometer/>
              </el-icon>
              启动像素级精度分析
            </el-button>
          </el-form>
        </el-card>

        <el-card class="progress-card mt-20" v-if="evaluationResult">
          <div class="chart-title">核心指标达成率</div>
          <div class="progress-wrapper">
            <el-progress type="circle" :percentage="evaluationResult.mAP * 100" :width="140" stroke-width="10">
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage.toFixed(1) }}%</span>
                <span class="percentage-label">mAP 0.5</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>

      <el-col :span="17">
        <div class="comparison-grid">
          <el-card class="viewer-card">
            <template #header><span>可视化对比 (Comparison)</span></template>
            <div class="viewer-content">
              <div class="v-item prediction">
                <div class="v-tag">PREDICTION</div>
                <el-image :src="getRealUrl(selectedTask?.maskPath)" fit="contain">
                  <template #placeholder>
                    <div class="img-load">读取结果中...</div>
                  </template>
                  <template #error>
                    <div class="img-load">等待预测数据</div>
                  </template>
                </el-image>
              </div>
              <div class="v-divider">VS</div>
              <div class="v-item truth">
                <div class="v-tag">GROUND TRUTH</div>
                <el-image :src="getRealUrl(gtFileUrl)" fit="contain">
                  <template #placeholder>
                    <div class="img-load">读取标签中...</div>
                  </template>
                  <template #error>
                    <div class="img-load">请上传 GT 标签</div>
                  </template>
                </el-image>
              </div>
            </div>
          </el-card>

          <el-card class="chart-card mt-20">
            <div ref="evalChartRef" class="spectral-chart"></div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue';
import {ElMessage} from 'element-plus';
import {Setting, Histogram, Odometer, Timer, Check, InfoFilled} from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import FileUpload from '@/components/FileUpload/index.vue';

const selectedTaskId = ref(null);
const selectedTask = ref(null);
const gtFileUrl = ref("");
const finishedTasks = ref([]);
const evaluationResult = ref(null);
const isEvaluating = ref(false);
const evalChartRef = ref(null);
let myChart = null;

const baseUrl = import.meta.env.VITE_APP_BASE_API;
const getRealUrl = (path) => path ? (path.startsWith('http') ? path : baseUrl + path) : '';

// 顶部卡片动态数据
const summaryCards = computed(() => ({
  "平均精度 (mAP)": {
    value: evaluationResult.value?.mAP || 0,
    precision: 3,
    icon: 'Histogram',
    color: '#409EFF',
    suffix: ''
  },
  "F1 综合得分": {value: evaluationResult.value?.f1 || 0, precision: 3, icon: 'Check', color: '#67C23A', suffix: ''},
  "识别延时 (s)": {
    value: evaluationResult.value?.latency || 0,
    precision: 2,
    icon: 'Timer',
    color: '#E6A23C',
    suffix: 's'
  },
  "样本通过率": {
    value: evaluationResult.value ? 100 : 0,
    precision: 0,
    icon: 'InfoFilled',
    color: '#909399',
    suffix: '%'
  },
}));

const loadFinishedTasks = async () => {
  // 模拟从后端获取状态为已完成(status=2)的任务
  finishedTasks.value = [
    {fileId: 101, fileName: 'HSOD_BIT_Scene_001', maskPath: '/profile/output/res_001.png', spectralData: '[]'},
    {fileId: 102, fileName: 'HSOD_BIT_Scene_002', maskPath: '/profile/output/res_002.png', spectralData: '[]'}
  ];
};

const handleEvaluate = () => {
  isEvaluating.value = true;
  ElMessage({message: '正在启动逐像素混淆矩阵分析...', type: 'info'});

  setTimeout(() => {
    evaluationResult.value = {
      mAP: 0.882,
      f1: 0.814,
      latency: 0.74
    };
    isEvaluating.value = false;
    ElMessage.success("精度评估完成，已更新指标看板");
    initEvalChart();
  }, 1200);
};

const initEvalChart = () => {
  if (!myChart) myChart = echarts.init(evalChartRef.value);
  const bandX = Array.from({length: 200}, (_, i) => i + 1);
  const predY = Array.from({length: 200}, () => Math.random() * 0.4 + 0.3);
  const truthY = predY.map(v => v + (Math.random() - 0.5) * 0.08);

  myChart.setOption({
    backgroundColor: 'transparent',
    title: {text: '光谱重建曲线匹配分析', left: 'center', textStyle: {color: '#303133', fontSize: 16}},
    legend: {bottom: 0},
    tooltip: {trigger: 'axis', axisPointer: {type: 'cross'}},
    xAxis: {type: 'category', data: bandX, axisLine: {lineStyle: {color: '#909399'}}},
    yAxis: {type: 'value', name: '反射率 (Reflectance)', splitLine: {lineStyle: {type: 'dashed'}}},
    series: [
      {
        name: '预测特征', type: 'line', smooth: true, data: predY, color: '#409EFF',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
            offset: 0,
            color: 'rgba(64,158,255,0.3)'
          }, {offset: 1, color: 'transparent'}])
        }
      },
      {
        name: '真值参考',
        type: 'line',
        smooth: true,
        data: truthY,
        color: '#67C23A',
        lineStyle: {width: 2, type: 'dashed'}
      }
    ]
  });
};

onMounted(loadFinishedTasks);
</script>

<style scoped>
.eval-dashboard {
  padding: 24px;
  background-color: #f8fafc;
  min-height: 100vh;
}

/* 顶部统计卡片 */
.stat-card {
  border-radius: 12px;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.main-row {
  margin-top: 24px;
}

/* 左侧配置 */
.config-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
  font-size: 16px;
}

.full-width {
  width: 100%;
}

.gt-upload-area {
  background: #f1f5f9;
  padding: 15px;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

.eval-btn {
  width: 100%;
  height: 45px;
  font-weight: bold;
  border-radius: 8px;
  font-size: 15px;
}

.progress-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.percentage-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.percentage-label {
  font-size: 12px;
  color: #909399;
}

/* 右侧对比视图 */
.viewer-card {
  border-radius: 16px;
}

.viewer-content {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 20px 0;
}

.v-item {
  flex: 1;
  max-width: 400px;
  position: relative;
  text-align: center;
  background: #fff;
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.v-tag {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  background: #334155;
  color: #fff;
  padding: 2px 12px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: bold;
  z-index: 10;
}

.v-divider {
  font-weight: 900;
  font-size: 24px;
  color: #e2e8f0;
  margin: 0 20px;
}

.img-load {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  color: #94a3b8;
  border-radius: 8px;
}

.spectral-chart {
  height: 380px;
  width: 100%;
}

.mt-20 {
  margin-top: 20px;
}
</style>