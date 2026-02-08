<template>
  <div class="spectral-lib-container">
    <el-row :gutter="20" style="height: 100%">

      <el-col :span="9" class="h-100">
        <el-card class="list-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><Collection/></el-icon> 端元列表 (Endmembers)</span>
              <el-button type="primary" size="small" icon="Plus" plain>导入数据</el-button>
            </div>
            <el-input
                v-model="searchQuery"
                placeholder="搜索物质名称/ID..."
                prefix-icon="Search"
                class="mt-10"
                clearable
            />
          </template>

          <el-table
              :data="libData"
              stripe
              height="calc(100vh - 240px)"
              highlight-current-row
              @row-click="handleRowClick"
              style="width: 100%; cursor: pointer;"
          >
            <el-table-column prop="id" label="ID" width="70"/>
            <el-table-column label="物质名称" min-width="120">
              <template #default="{ row }">
                <div class="name-cell">
                  <span class="font-bold">{{ row.name }}</span>
                  <el-tag size="small" :type="row.typeTag" effect="plain">{{ row.category }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="波形预览" width="140" align="center">
              <template #default="scope">
                <div :id="'mini-chart-' + scope.$index" class="mini-chart-box"></div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="15" class="h-100">
        <div v-if="selectedItem" class="detail-dashboard">
          <el-card class="info-card mb-20" shadow="hover">
            <el-descriptions :title="selectedItem.name + ' - 光谱特征详情'" :column="3" border>
              <el-descriptions-item label="入库ID">{{ selectedItem.id }}</el-descriptions-item>
              <el-descriptions-item label="采样环境">
                <el-tag size="small">自然光 11:00 AM</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ selectedItem.updateTime }}</el-descriptions-item>
              <el-descriptions-item label="光谱熵">0.864</el-descriptions-item>
              <el-descriptions-item label="主要波峰">{{ selectedItem.peak }} nm</el-descriptions-item>
              <el-descriptions-item label="操作">
                <el-button type="primary" link icon="Download">导出CSV</el-button>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="chart-card mb-20" shadow="hover">
            <template #header>
              <div class="chart-header">
                <span><el-icon><TrendCharts/></el-icon> 200波段全谱反射率曲线 (Reflectance)</span>
                <el-radio-group v-model="chartMode" size="small" @change="updateMainChart">
                  <el-radio-button label="raw">原始值</el-radio-button>
                  <el-radio-button label="smooth">平滑去噪</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div id="main-spectral-chart" style="height: 350px; width: 100%;"></div>
          </el-card>

          <el-row :gutter="20">
            <el-col :span="10">
              <el-card class="chart-card" shadow="hover">
                <div slot="header" class="chart-header-small">特征指纹 (Feature Fingerprint)</div>
                <div id="radar-chart" style="height: 250px;"></div>
              </el-card>
            </el-col>
            <el-col :span="14">
              <el-card class="chart-card" shadow="hover">
                <div slot="header" class="chart-header-small">库内相似物质匹配 (Top 5)</div>
                <div id="similarity-chart" style="height: 250px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div v-else class="empty-state">
          <el-empty description="请点击左侧列表查看详细光谱数据"/>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, onMounted, nextTick, watch} from 'vue';
import {Collection, Search, TrendCharts, Plus} from '@element-plus/icons-vue';
import * as echarts from 'echarts';

// --- 模拟数据生成器 ---
// 模拟不同物质的光谱曲线趋势
const generateCurve = (type) => {
  const data = [];
  for (let i = 0; i < 200; i++) {
    let val = 0;
    // 模拟植被：红边效应（在波段50-80左右陡峭上升）
    if (type === 'veg') {
      if (i < 50) val = 0.05 + Math.random() * 0.02;
      else if (i < 80) val = 0.05 + (i - 50) * 0.015;
      else val = 0.5 + Math.random() * 0.05 - (i - 80) * 0.001;
    }
    // 模拟金属：整体较低且平坦，缓慢上升
    else if (type === 'metal') {
      val = 0.15 + (i * 0.001) + Math.random() * 0.03;
    }
    // 模拟伪装网：模仿植被但有差异
    else if (type === 'net') {
      if (i < 50) val = 0.08 + Math.random() * 0.02;
      else if (i < 80) val = 0.08 + (i - 50) * 0.01;
      else val = 0.35 + Math.sin(i / 20) * 0.05;
    }
    data.push(val.toFixed(4));
  }
  return data;
};

const libData = ref([
  {
    id: 'S001',
    name: '绿色植被 (草地)',
    category: '自然背景',
    typeTag: 'success',
    updateTime: '2026-02-05',
    peak: '780',
    data: generateCurve('veg')
  },
  {
    id: 'S002',
    name: '金属板 (涂层)',
    category: '人造目标',
    typeTag: 'danger',
    updateTime: '2026-02-06',
    peak: 'N/A',
    data: generateCurve('metal')
  },
  {
    id: 'S003',
    name: '伪装网 (丛林)',
    category: '干扰物',
    typeTag: 'warning',
    updateTime: '2026-02-04',
    peak: '650',
    data: generateCurve('net')
  },
  {
    id: 'S004',
    name: '枯黄落叶',
    category: '自然背景',
    typeTag: 'info',
    updateTime: '2026-02-01',
    peak: '600',
    data: generateCurve('veg').map(v => v * 0.8)
  }, // 变种
  {
    id: 'S005',
    name: '混凝土路面',
    category: '人造目标',
    typeTag: 'info',
    updateTime: '2026-01-20',
    peak: 'N/A',
    data: generateCurve('metal').map(v => v * 1.5)
  },
]);

const searchQuery = ref('');
const selectedItem = ref(null);
const chartMode = ref('raw');
let mainChartInstance = null;
let radarChartInstance = null;
let barChartInstance = null;

// 初始化微缩图 (Sparklines)
const initMiniCharts = () => {
  nextTick(() => {
    libData.value.forEach((item, index) => {
      const dom = document.getElementById(`mini-chart-${index}`);
      if (dom) {
        // 防止重复初始化
        const existChart = echarts.getInstanceByDom(dom);
        if (existChart) existChart.dispose();

        const chart = echarts.init(dom);
        chart.setOption({
          grid: {top: 2, bottom: 2, left: 0, right: 0},
          xAxis: {type: 'category', show: false},
          yAxis: {type: 'value', show: false, min: 0, max: 1},
          series: [{
            data: item.data, // 只取前20个点做缩略? 不，取采样
            type: 'line',
            showSymbol: false,
            lineStyle: {width: 1.5, color: '#409EFF'},
            areaStyle: {opacity: 0.1, color: '#409EFF'}
          }]
        });
      }
    });
  });
};

// 点击行处理
const handleRowClick = (row) => {
  selectedItem.value = row;
  nextTick(() => {
    renderDetailCharts();
  });
};

// 渲染右侧所有详细图表
const renderDetailCharts = () => {
  if (!selectedItem.value) return;

  // 1. 主光谱曲线图
  const mainDom = document.getElementById('main-spectral-chart');
  if (mainDom) {
    if (mainChartInstance) mainChartInstance.dispose();
    mainChartInstance = echarts.init(mainDom);

    const xData = Array.from({length: 200}, (_, i) => i + 1);
    mainChartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: {type: 'cross'},
        formatter: (params) => `波段 ${params[0].name}<br/>反射率: ${params[0].value}`
      },
      grid: {left: '3%', right: '3%', bottom: '10%', top: '10%', containLabel: true},
      dataZoom: [{type: 'inside'}, {type: 'slider', bottom: 0}],
      xAxis: {type: 'category', data: xData, name: 'Band'},
      yAxis: {type: 'value', name: 'Reflectance', min: 0, max: 1},
      series: [{
        name: selectedItem.value.name,
        type: 'line',
        smooth: chartMode.value === 'smooth',
        symbol: 'none',
        data: selectedItem.value.data,
        lineStyle: {width: 2, color: '#409EFF'},
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {offset: 0, color: 'rgba(64, 158, 255, 0.3)'},
            {offset: 1, color: 'rgba(64, 158, 255, 0.05)'}
          ])
        }
      }]
    });
  }

  // 2. 雷达图 (特征指纹)
  const radarDom = document.getElementById('radar-chart');
  if (radarDom) {
    if (radarChartInstance) radarChartInstance.dispose();
    radarChartInstance = echarts.init(radarDom);
    radarChartInstance.setOption({
      tooltip: {},
      radar: {
        indicator: [
          {name: '峰值强度', max: 1},
          {name: '吸收深度', max: 1},
          {name: '波形熵', max: 1},
          {name: '红边斜率', max: 1},
          {name: '均值', max: 1},
          {name: '方差', max: 0.1}
        ],
        radius: '65%'
      },
      series: [{
        name: '特征指标',
        type: 'radar',
        data: [{
          value: [
            Math.random() * 0.5 + 0.5,
            Math.random(),
            Math.random(),
            Math.random(),
            Math.random(),
            Math.random() * 0.05
          ],
          name: selectedItem.value.name,
          areaStyle: {color: 'rgba(230, 162, 60, 0.4)'},
          lineStyle: {color: '#E6A23C'}
        }]
      }]
    });
  }

  // 3. 柱状图 (相似度)
  const barDom = document.getElementById('similarity-chart');
  if (barDom) {
    if (barChartInstance) barChartInstance.dispose();
    barChartInstance = echarts.init(barDom);
    barChartInstance.setOption({
      tooltip: {trigger: 'axis', axisPointer: {type: 'shadow'}},
      grid: {left: '3%', right: '4%', bottom: '3%', containLabel: true},
      xAxis: {type: 'value', show: false},
      yAxis: {
        type: 'category',
        data: ['标准植被库', '金属-铝', '伪装漆-A型', '土壤-干燥', '未知目标'],
        inverse: true // 排名从上到下
      },
      series: [{
        name: '匹配度',
        type: 'bar',
        data: [0.98, 0.45, 0.32, 0.15, 0.05],
        label: {show: true, position: 'right', formatter: '{@score}'},
        itemStyle: {
          color: (params) => {
            return params.dataIndex === 0 ? '#67C23A' : '#909399';
          },
          borderRadius: [0, 4, 4, 0]
        },
        barWidth: 15
      }]
    });
  }
};

const updateMainChart = () => {
  renderDetailCharts(); // 简单重绘
};

onMounted(() => {
  initMiniCharts();
  // 默认选中第一行
  if (libData.value.length > 0) {
    handleRowClick(libData.value[0]);
  }

  window.addEventListener('resize', () => {
    mainChartInstance?.resize();
    radarChartInstance?.resize();
    barChartInstance?.resize();
    // 列表里的微缩图也应该 resize，但出于性能通常只重绘可见的
  });
});
</script>

<style scoped>
.spectral-lib-container {
  padding: 20px;
  background-color: #f0f2f5;
  height: calc(100vh - 84px); /* 适应一般后台布局 */
  overflow: hidden;
}

.h-100 {
  height: 100%;
}

.mt-10 {
  margin-top: 10px;
}

.mb-20 {
  margin-bottom: 20px;
}

.font-bold {
  font-weight: bold;
}

/* 左侧列表样式 */
.list-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mini-chart-box {
  width: 100%;
  height: 40px; /* 稍微调小一点，适合表格 */
}

/* 右侧详情样式 */
.detail-dashboard {
  height: 100%;
  overflow-y: auto; /* 右侧内容多时可滚动 */
  padding-right: 5px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #303133;
}

.chart-header-small {
  font-weight: bold;
  font-size: 14px;
  color: #606266;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 8px;
}
</style>