<template>
  <div class="detection-container">
    <el-row :gutter="20">
      <el-col :span="9">
        <el-card header="数据成对导入">
          <el-alert title="请确保左右两侧文件上传的顺序完全一致" type="warning" show-icon :closable="false"/>

          <div class="dual-upload-wrapper">
            <div class="upload-column">
              <p class="upload-label">1. 原始伪彩图 (.jpg)</p>
              <FileUpload
                  v-model="picFilesStr"
                  :file-type="['jpg', 'jpeg', 'png']"
                  :limit="20"
                  :file-size="10"
                  :is-show-tip="true"
              />
            </div>

            <div class="upload-column">
              <p class="upload-label">2. 高光谱文件 (.mat)</p>
              <FileUpload
                  v-model="matFilesStr"
                  :file-type="['mat']"
                  :limit="20"
                  :file-size="500"
                  :is-show-tip="true"
              />
            </div>
          </div>

          <el-button
              type="success"
              @click="pairByOrder"
              :disabled="!canPair"
              style="width: 100%; margin-top: 20px;"
          >
            按顺序配对并开始识别
          </el-button>
        </el-card>

        <el-card class="mt-20" header="检测任务列表">
          <el-table ref="taskTable" :data="pairedTasks" highlight-current-row @current-change="handleTaskSelect">
            <el-table-column type="index" label="序号" width="60"/>
            <el-table-column prop="name" label="任务名称" show-overflow-tooltip/>
            <el-table-column label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.processed ? 'success' : 'info'">
                  {{ scope.row.processed ? '完成' : '待机' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="15">
        <el-card v-if="currentTask" class="result-detail-card">
          <template #header>
            <div class="result-header">
              <span>正在查看：{{ currentTask.name }}</span>
              <div class="metrics-tags" v-if="currentTask.processed">
                <el-tag size="small">mAP: {{ currentTask.mAP }}</el-tag>
                <el-tag size="small" type="warning">F1: {{ currentTask.f1 }}</el-tag>
                <el-tag size="small" type="info">推理速度: {{ currentTask.latency }}s</el-tag>
              </div>
              <el-button v-else type="primary" size="small" @click="runInference(currentTask)" :loading="isProcessing">
                执行当前识别
              </el-button>
            </div>
          </template>

          <div class="viewer-layout">
            <div class="view-box">
              <p>原始高光谱伪彩图</p>
              <el-image :src="currentTask.jpgUrl" fit="contain">
                <template #error>
                  <div class="img-load">无预览图</div>
                </template>
              </el-image>
            </div>
            <div class="view-box highlight">
              <p>显著性检测结果 (Mask)</p>
              <el-image :src="currentTask.maskUrl" fit="contain">
                <template #placeholder>
                  <div class="img-load">{{ currentTask.processed ? '渲染中...' : '等待识别' }}</div>
                </template>
                <template #error>
                  <div class="img-load">等待结果</div>
                </template>
              </el-image>
            </div>
          </div>

          <div ref="chartRef" class="spectral-chart"></div>
        </el-card>

        <el-empty v-else description="请上传并点击左侧列表中的任务进行识别预览"/>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, computed, nextTick, onMounted} from 'vue';
import {ElMessage} from 'element-plus';
import * as echarts from 'echarts';
import FileUpload from '@/components/FileUpload/index.vue';
import {demo} from '@/api/login.js'
// 状态变量
const picFilesStr = ref(""); // 接收 FileUpload 的逗号分隔字符串
const matFilesStr = ref("");
const pairedTasks = ref([]);
const currentTask = ref(null);
const isProcessing = ref(false);
const chartRef = ref(null);
const taskTable = ref(null);
let myChart = null;

// 获取 Base URL 用于拼接图片路径（如果后端返回的是相对路径）
const baseUrl = import.meta.env.VITE_APP_BASE_API || '';

onMounted(() => {
  demo()
})

// 计算是否可以配对
const canPair = computed(() => {
  if (!picFilesStr.value || !matFilesStr.value) return false;
  const pics = picFilesStr.value.split(',');
  const mats = matFilesStr.value.split(',');
  return pics.length > 0 && pics.length === mats.length;
});

// 辅助函数：从 URL/路径中提取文件名作为任务名
const getFileName = (path) => {
  if (!path) return "Unknown";
  // 移除路径前缀
  const fullName = path.split('/').pop();
  // 移除扩展名
  return fullName.split('.').slice(0, -1).join('.');
};

// 辅助函数：处理 URL
const resolveUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http') || path.startsWith('blob')) return path;
  return `${baseUrl}${path}`; // 拼接后端基础路径
};

// 核心逻辑：解析字符串并配对
const pairByOrder = () => {
  const picList = picFilesStr.value ? picFilesStr.value.split(',') : [];
  const matList = matFilesStr.value ? matFilesStr.value.split(',') : [];

  if (picList.length !== matList.length) {
    ElMessage.error(`数量不匹配：图片 ${picList.length} 张，MAT文件 ${matList.length} 个`);
    return;
  }

  pairedTasks.value = picList.map((picPath, index) => {
    const taskName = getFileName(picPath); // 从路径提取文件名
    return {
      name: taskName,
      jpgUrl: resolveUrl(picPath), // 使用上传后返回的 URL
      matPath: matList[index],     // 保存 mat 文件路径供后端调用
      maskUrl: '',
      mAP: '0.00',
      f1: '0.00',
      latency: '0.0',
      processed: false,
      spectralData: []
    }
  });

  ElMessage.success(`成功配对 ${pairedTasks.value.length} 组数据`);

  // 自动选中第一条并开始模拟识别
  if (pairedTasks.value.length > 0) {
    nextTick(() => {
      taskTable.value.setCurrentRow(pairedTasks.value[0]);
      runInference(pairedTasks.value[0]);
    });
  }
};

const handleTaskSelect = (val) => {
  currentTask.value = val;
  nextTick(() => {
    initChart();
    if (val && val.processed) {
      updateChart(val.spectralData);
    }
  });
};

const runInference = (task) => {
  if (!task || task.processed) return;
  isProcessing.value = true;

  // 模拟后端推理过程
  setTimeout(() => {
    task.processed = true;
    task.mAP = (0.76 + Math.random() * 0.1).toFixed(2);
    task.f1 = (0.71 + Math.random() * 0.1).toFixed(2);
    task.latency = (1.2 + Math.random() * 1.5).toFixed(1);

    // 模拟结果：直接使用原图 URL 作为 Mask 演示
    task.maskUrl = task.jpgUrl;

    // 模拟光谱数据
    task.spectralData = Array.from({length: 200}, () => (Math.random() * 0.6 + 0.1).toFixed(4));

    if (currentTask.value === task) {
      updateChart(task.spectralData);
    }
    isProcessing.value = false;
    ElMessage.success(`${task.name} 识别完成`);
  }, 1800);
};

const initChart = () => {
  if (!chartRef.value) return;
  if (myChart) myChart.dispose();
  myChart = echarts.init(chartRef.value);
  myChart.setOption({
    title: {text: '200波段光谱特征曲线 (HSOD-BIT)', textStyle: {fontSize: 14}},
    tooltip: {trigger: 'axis'},
    grid: {left: '3%', right: '4%', bottom: '3%', containLabel: true},
    xAxis: {name: '波段', type: 'category', data: Array.from({length: 200}, (_, i) => i + 1)},
    yAxis: {name: '反射率', type: 'value', min: 0, max: 1},
    series: [{name: '特征指纹', type: 'line', smooth: true, data: [], color: '#409EFF', areaStyle: {opacity: 0.1}}]
  });
};

const updateChart = (data) => {
  if (myChart) {
    myChart.setOption({series: [{data: data}]});
  }
};

</script>

<style scoped>
.detection-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.dual-upload-wrapper {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  gap: 10px;
}

.upload-column {
  flex: 1;
  padding: 10px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  background: #fff;
}

.upload-label {
  font-size: 12px;
  font-weight: bold;
  color: #606266;
  margin-bottom: 10px;
}

.mt-20 {
  margin-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.metrics-tags {
  display: flex;
  gap: 10px;
}

.viewer-layout {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.view-box {
  flex: 1;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  text-align: center;
  background: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.view-box p {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: bold;
}

.spectral-chart {
  height: 320px;
  margin-top: 20px;
  width: 100%;
}

.img-load {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #c0c4cc;
  border-radius: 4px;
}
</style>