<template>
  <div class="eval-dashboard">
    <el-row :gutter="20" class="stat-row">
      <el-col :span="4" v-for="(val, label) in summaryCards" :key="label">
        <el-card shadow="hover" class="stat-card">
          <el-statistic :value="val.value" :precision="val.precision" :suffix="val.suffix">
            <template #title>
              <div class="stat-title">
                <el-icon :color="val.color" :size="18">
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
        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon>
                <Setting/>
              </el-icon>
              <span>评估控制台</span>
            </div>
          </template>

          <el-form label-position="top">
            <el-form-item label="选择已完成的高光谱任务">
              <el-select
                  v-model="selectedTaskId"
                  placeholder="请选择检测记录"
                  @change="handleTaskChange"
                  class="full-width"
                  filterable
              >
                <el-option
                    v-for="t in finishedTasks"
                    :key="t.taskId"
                    :label="`${t.fileName || t.taskName} (ID:${t.taskId})`"
                    :value="t.taskId"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="上传 Ground Truth (真实标签)">
              <div class="gt-upload-area">
                <file-upload
                    v-model="gtFileUrl"
                    :limit="1"
                    :file-size="10"
                    :file-type="['png','jpg','jpeg','bmp']"
                />
              </div>
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="isRenew">强制重新计算 (忽略已有缓存)</el-checkbox>
            </el-form-item>

            <el-button
                type="primary"
                class="eval-btn"
                @click="handleEvaluate"
                :loading="isEvaluating"
                :disabled="!selectedTaskId || !gtFileUrl"
            >
              <el-icon style="margin-right: 5px">
                <Odometer/>
              </el-icon>
              启动像素级精度分析
            </el-button>
          </el-form>
        </el-card>

        <transition name="el-fade-in">
          <el-card class="progress-card mt-20" v-if="evaluationResult" shadow="hover">
            <div class="chart-title">核心指标达成率</div>
            <div class="progress-wrapper">
              <el-progress type="circle" :percentage="(evaluationResult.f1 || 0) * 100" :width="140" stroke-width="12"
                           color="#67C23A">
                <template #default="{ percentage }">
                  <span class="percentage-value">{{ percentage.toFixed(1) }}%</span>
                  <span class="percentage-label">F1-Score</span>
                </template>
              </el-progress>
            </div>
            <div style="margin-top: 15px; font-size: 13px; color: #666;">
              <div>AUC: {{ evaluationResult.auc?.toFixed(3) }}</div>
              <div>MAE: {{ evaluationResult.mae?.toFixed(3) }}</div>
            </div>
          </el-card>
        </transition>
      </el-col>

      <el-col :span="17">
        <div class="comparison-grid">
          <el-card class="viewer-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon>
                  <Picture/>
                </el-icon>
                <span>可视化对比 (Visual Comparison)</span>
              </div>
            </template>
            <div class="viewer-content">
              <div class="v-item prediction">
                <div class="v-tag predict-tag">AI PREDICTION</div>
                <el-image
                    :src="getRealUrl(selectedTask?.maskPath)"
                    fit="contain"
                    class="result-image"
                    :preview-src-list="[getRealUrl(selectedTask?.maskPath)]"
                >
                  <template #placeholder>
                    <div class="img-load">加载中...</div>
                  </template>
                  <template #error>
                    <div class="img-load error-state">
                      <el-icon :size="30">
                        <Warning/>
                      </el-icon>
                      <p>暂无预测结果</p>
                    </div>
                  </template>
                </el-image>
              </div>

              <div class="v-divider">VS</div>

              <div class="v-item truth">
                <div class="v-tag truth-tag">GROUND TRUTH</div>
                <el-image
                    :src="getRealUrl(gtFileUrl)"
                    fit="contain"
                    class="result-image"
                    :preview-src-list="[getRealUrl(gtFileUrl)]"
                >
                  <template #placeholder>
                    <div class="img-load">加载中...</div>
                  </template>
                  <template #error>
                    <div class="img-load empty-state">
                      <el-icon :size="30">
                        <UploadFilled/>
                      </el-icon>
                      <p>请上传 GT 标签</p>
                    </div>
                  </template>
                </el-image>
              </div>
            </div>
          </el-card>

          <el-card class="chart-card mt-20" shadow="never">
            <div ref="evalChartRef" class="spectral-chart"></div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, onMounted, computed, nextTick} from 'vue';
import {ElMessage} from 'element-plus';
import {
  Setting, Histogram, Odometer, Timer, Check, InfoFilled,
  Picture, Warning, UploadFilled, TrendCharts, Aim
} from '@element-plus/icons-vue';
import * as echarts from 'echarts';

// 引入组件和接口
import FileUpload from '@/components/FileUpload/index.vue';
import {getList, evaluate} from '@/api/predict.js'; // 确保引入了 evaluate

// --- 状态定义 ---
const selectedTaskId = ref(null);
const selectedTask = ref(null);
const gtFileUrl = ref("");
const isRenew = ref(false); // 控制是否强制重新计算
const finishedTasks = ref([]);
const evaluationResult = ref(null);
const isEvaluating = ref(false);
const evalChartRef = ref(null);
let myChart = null;

const baseUrl = import.meta.env.VITE_APP_BASE_API;

const getRealUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http') || path.startsWith('https')) return path;
  return baseUrl + path;
};

// --- 核心指标映射 (根据后端 DetectionTask 新增字段) ---
const summaryCards = computed(() => ({
  "F1-Score": {
    value: evaluationResult.value?.f1 || 0,
    precision: 3,
    icon: 'Check',
    color: '#67C23A',
    suffix: ''
  },
  "AUC (Area Under Curve)": {
    value: evaluationResult.value?.auc || 0,
    precision: 3,
    icon: 'TrendCharts',
    color: '#409EFF',
    suffix: ''
  },
  "MAE (Mean Abs Error)": {
    value: evaluationResult.value?.mae || 0,
    precision: 3,
    icon: 'Odometer',
    color: '#E6A23C', // MAE 越低越好，也可以用红色或橙色表示差异
    suffix: ''
  },
  "CC (Correlation)": {
    value: evaluationResult.value?.cc || 0,
    precision: 3,
    icon: 'Histogram',
    color: '#409EFF',
    suffix: ''
  },
  "NSS (ScanPath)": {
    value: evaluationResult.value?.nss || 0,
    precision: 3,
    icon: 'Aim',
    color: '#909399',
    suffix: ''
  },
  "Recall": {
    value: evaluationResult.value?.rec || 0,
    precision: 3,
    icon: 'InfoFilled',
    color: '#909399',
    suffix: ''
  }
}));

// --- 业务逻辑 ---

// 1. 加载已完成任务
const loadFinishedTasks = async () => {
  try {
    const res = await getList({});
    if (res.code === 200 && res.data) {
      // 过滤 status === 2 的任务
      finishedTasks.value = res.data.filter(item => item.status === 2);
    }
  } catch (error) {
    ElMessage.error("任务列表加载失败");
  }
};

// 2. 切换任务处理
const handleTaskChange = async (val) => {
  if (!val) return;
  // 重置状态
  evaluationResult.value = null;
  // 注意：gtFileUrl 不一定要清空，用户可能想用同一张 GT 测不同的算法结果

  try {
    const res = await getList({taskId: val});
    if (res.code === 200 && res.data && res.data.length > 0) {
      selectedTask.value = res.data[0];

      // 如果任务之前已经评估过（有 gtFileId），可以回显数据
      // 这里根据你的需求，也可以选择自动填充 gtFileUrl

      // 渲染光谱图
      if (selectedTask.value.spectralData) {
        try {
          const specData = JSON.parse(selectedTask.value.spectralData);
          initEvalChart(specData);
        } catch (e) {
          console.warn("光谱数据解析异常");
        }
      }
    }
  } catch (error) {
    ElMessage.error("获取任务详情失败");
  }
};

// 3. 执行评估 (对接后端 evaluate 接口)
const handleEvaluate = async () => {
  if (!selectedTaskId.value || !gtFileUrl.value) {
    ElMessage.warning("请先选择任务并上传 Ground Truth 标签");
    return;
  }

  isEvaluating.value = true;
  ElMessage.info("正在提交后端进行精度计算...");

  try {
    // 构造后端需要的 Map 参数
    const params = {
      taskID: selectedTaskId.value,
      isRenew: isRenew.value ? 1 : 0,
      gtPath: gtFileUrl.value // 假设 FileUpload 组件返回的是逗号分隔的路径，后端只取一个
    };

    const res = await evaluate(params);

    if (res.code === 200) {
      const taskData = res.data; // 后端返回更新后的 task 对象

      if (res.msg === "已存在数据") {
        ElMessage.info("检测到已有评估数据，已直接加载（如需重算请勾选强制重算）");
      } else {
        ElMessage.success("精度评估计算完成！");
      }

      // 更新前端显示的评估结果
      evaluationResult.value = {
        f1: taskData.f1,
        mae: taskData.mae,
        auc: taskData.auc,
        cc: taskData.cc,
        nss: taskData.nss,
        rec: taskData.rec,
        pre: taskData.pre,
        latency: taskData.latency // 保持原有字段
      };

      // 刷新选中的任务对象，确保图片等信息同步
      selectedTask.value = taskData;

      // 如果有光谱数据，刷新图表
      if (taskData.spectralData) {
        initEvalChart(JSON.parse(taskData.spectralData));
      }

    } else {
      ElMessage.error(res.msg || "评估失败");
    }
  } catch (error) {
    console.error(error);
    ElMessage.error("评估接口请求异常");
  } finally {
    isEvaluating.value = false;
  }
};

// 4. 图表初始化 (保持不变，略作样式调整)
const initEvalChart = (realData) => {
  nextTick(() => {
    if (!evalChartRef.value) return;
    if (!myChart) {
      myChart = echarts.init(evalChartRef.value);
      window.addEventListener('resize', () => myChart.resize());
    }

    const bandCount = 200;
    const xAxisData = Array.from({length: bandCount}, (_, i) => i + 1);
    const predData = realData || Array.from({length: bandCount}, () => 0);
    // 这里如果没有真实的 GT 光谱，可以暂时不显示第二条线，或者显示一条基准线

    const option = {
      backgroundColor: 'transparent',
      title: {
        text: '光谱一致性分析',
        left: 'center',
        textStyle: {color: '#606266', fontSize: 16}
      },
      tooltip: {trigger: 'axis'},
      legend: {bottom: 10, data: ['预测目标光谱']},
      grid: {left: '3%', right: '4%', bottom: '10%', containLabel: true},
      xAxis: {
        type: 'category',
        data: xAxisData,
        name: '波段'
      },
      yAxis: {type: 'value', name: '反射率'},
      series: [
        {
          name: '预测目标光谱',
          type: 'line',
          smooth: true,
          showSymbol: false,
          itemStyle: {color: '#409EFF'},
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {offset: 0, color: 'rgba(64, 158, 255, 0.4)'},
              {offset: 1, color: 'rgba(64, 158, 255, 0.05)'}
            ])
          },
          data: predData
        }
      ]
    };
    myChart.setOption(option);
  });
};

onMounted(() => {
  loadFinishedTasks();
});
</script>

<style scoped>
.eval-dashboard {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.stat-row .el-col {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  border: none;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
  margin-bottom: 5px;
}

.main-row {
  margin-top: 5px;
}

.mt-20 {
  margin-top: 20px;
}

/* 左侧配置区 */
.config-card {
  border-radius: 8px;
  border: none;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  font-size: 16px;
  color: #303133;
}

.full-width {
  width: 100%;
}

.gt-upload-area {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 6px;
  border: 1px dashed #dcdfe6;
  text-align: center;
}

.eval-btn {
  width: 100%;
  padding: 12px;
  font-weight: bold;
  margin-top: 10px;
}

/* 进度卡片 */
.progress-card {
  border-radius: 8px;
  border: none;
  text-align: center;
}

.chart-title {
  font-size: 15px;
  font-weight: bold;
  margin-bottom: 20px;
}

.progress-wrapper {
  display: flex;
  justify-content: center;
}

.percentage-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
}

.percentage-label {
  font-size: 12px;
  color: #909399;
}

/* 对比视图 */
.viewer-card {
  border-radius: 8px;
  border: none;
  background: #fff;
}

.viewer-content {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 20px;
  background: #fcfcfc;
}

.v-item {
  flex: 1;
  max-width: 45%;
  position: relative;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.v-tag {
  position: absolute;
  top: 5px;
  left: 10px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  color: #fff;
  z-index: 5;
}

.predict-tag {
  background: rgba(64, 158, 255, 0.9);
}

.truth-tag {
  background: rgba(103, 194, 58, 0.9);
}

.v-divider {
  font-weight: 900;
  color: #dcdfe6;
  margin: 0 15px;
}

.result-image {
  width: 100%;
  height: 300px;
  display: block;
}

.img-load {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
}

.error-state {
  color: #f56c6c;
}

/* 图表 */
.chart-card {
  border-radius: 8px;
  border: none;
}

.spectral-chart {
  width: 100%;
  height: 350px;
}
</style>