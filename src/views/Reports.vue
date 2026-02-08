<template>
  <div class="reports-container">
    <el-card class="box-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="20" color="#409EFF">
              <Document/>
            </el-icon>
            <span class="title">全量识别报告记录</span>
          </div>
          <div class="header-right">
            <el-input
                v-model="searchKeyword"
                placeholder="搜索文件名/任务ID"
                prefix-icon="Search"
                style="width: 200px; margin-right: 10px;"
                clearable
            />
            <el-button type="primary" @click="fetchReports" :loading="loading" icon="Refresh">刷新列表</el-button>
          </div>
        </div>
      </template>

      <el-table
          :data="filteredList"
          stripe
          style="width: 100%"
          v-loading="loading"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="taskId" label="任务ID" width="100" align="center" sortable/>

        <el-table-column label="源数据文件" min-width="180">
          <template #default="{ row }">
            <div class="file-info">
              <el-icon>
                <Files/>
              </el-icon>
              <span>{{ row.jpgFile.fileName || row.taskName || `Task-${row.taskId}` }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="任务状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="包含真值(GT)" width="150" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.gtFileId || row.gtFile" type="success" size="default" effect="plain">
              已上传
            </el-tag>
            <span v-else style="color: #909399; font-size: 12px;">-</span>
          </template>
        </el-table-column>

        <el-table-column label="核心指标 (mae / F1)" width="220" align="center">
          <template #default="{ row }">
            <div class="metrics-tags" v-if="row.status === 2">
              <el-tooltip content="平均绝对误差 (mAE)" placement="top">
                <el-tag :type="getScoreType(row.mae)" effect="dark" size="small">
                  mae: {{ formatNum(row.mae) }}
                </el-tag>
              </el-tooltip>
              <el-tooltip content="F1-Score" placement="top">
                <el-tag :type="getScoreType(row.f1)" effect="light" size="small">
                  F1: {{ formatNum(row.f1) }}
                </el-tag>
              </el-tooltip>
            </div>
            <span v-else class="text-gray">待生成</span>
          </template>
        </el-table-column>

        <el-table-column prop="latency" label="耗时(s)" width="100" align="center">
          <template #default="{ row }">
            {{ row.latency ? row.latency.toFixed(2) : '-' }}s
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="scope">
            <el-button type="primary" link icon="View" @click="viewDetail(scope.row)">
              详情
            </el-button>
            <el-divider direction="vertical"/>
            <el-button
                type="warning"
                link
                icon="Download"
                @click="exportPDF(scope.row)"
                :disabled="scope.row.status !== 2"
            >
              导出报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-footer">
        <el-pagination layout="total, prev, pager, next" :total="filteredList.length"/>
      </div>
    </el-card>

    <el-dialog
        v-model="dialogVisible"
        title="高光谱检测任务详情报告"
        width="75%"
        destroy-on-close
        top="5vh"
    >
      <div class="detail-container" v-if="currentReport">
        <el-descriptions title="基础元数据" :column="3" border class="mb-20">
          <el-descriptions-item label="任务编号">{{ currentReport.taskId }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{
              currentReport.fileName || currentReport.taskName
            }}
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(currentReport.status)" size="medium">{{
                getStatusText(currentReport.status)
              }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="平均绝对误差 (mae)">
            <span class="score-text">{{ formatNum(currentReport.mae) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="F1-Score">
            <span class="score-text">{{ formatNum(currentReport.f1) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="推理耗时">{{ currentReport.latency || '-' }} 秒</el-descriptions-item>
        </el-descriptions>

        <div class="image-section">
          <div class="section-title">可视化检测结果</div>
          <div class="image-grid">
            <div class="img-card">
              <div class="img-header">原始 RGB 伪彩图</div>
              <el-image
                  :src="getRealUrl(currentReport.jpgFile?.storagePath)"
                  fit="contain"
                  :preview-src-list="[getRealUrl(currentReport.jpgFile?.storagePath)]"
                  class="detail-img"
              >
                <template #error>
                  <div class="img-err">无预览图</div>
                </template>
              </el-image>
            </div>

            <div class="img-card">
              <div class="img-header">预测显著性掩膜 (Prediction)</div>
              <div v-if="currentReport.status === 2">
                <el-image
                    :src="getRealUrl(currentReport.maskPath)"
                    fit="contain"
                    :preview-src-list="[getRealUrl(currentReport.maskPath)]"
                    class="detail-img"
                >
                  <template #error>
                    <div class="img-err">加载失败</div>
                  </template>
                </el-image>
              </div>
              <div v-else class="img-err">
                {{ getStatusText(currentReport.status) }}...
              </div>
            </div>

            <div class="img-card" v-if="currentReport.gtFileId || currentReport.gtFile">
              <div class="img-header">真实标签 (Ground Truth)</div>
              <el-image
                  :src="getRealUrl(currentReport.gtFile?.storagePath)"
                  fit="contain"
                  :preview-src-list="[getRealUrl(currentReport.gtFile?.storagePath)]"
                  class="detail-img"
              >
                <template #error>
                  <div class="img-err">GT加载失败</div>
                </template>
              </el-image>
            </div>
          </div>
        </div>
        <div class="cube-section mt-20">
          <div class="section-title">3D 光谱立方体可视化 (Spectral Cube)</div>
          <hyper-cube-viewer
              v-if="dialogVisible && currentReport"
              :mat="currentReport.matFile||currentReport.matFileId"
          />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="exportPDF(currentReport)" :disabled="currentReport?.status !== 2">下载 PDF 报告</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue';
import {ElMessage} from 'element-plus';
import {Document, Refresh, Search, Files, View, Download, Check} from '@element-plus/icons-vue';
import {getList} from '@/api/predict';
import {exportReportPdf} from '@/api/report';
import HyperCubeViewer from '@/components/HyperCubeViewer/index.vue';

const loading = ref(false);
const reportList = ref([]);
const searchKeyword = ref('');
const dialogVisible = ref(false);
const currentReport = ref(null);

const baseUrl = import.meta.env.VITE_APP_BASE_API;

// 路径处理工具
const getRealUrl = (path) => {
  if (!path) return '';
  // 确保反斜杠被替换，防止Windows路径问题
  path = path.replace(/\\/g, '/');
  if (path.startsWith('http') || path.startsWith('https')) return path;
  return baseUrl + path;
};

const formatNum = (num) => {
  if (num === null || num === undefined) return '0.000';
  return Number(num).toFixed(3);
};

// 状态映射
const getStatusType = (status) => {
  if (status === 2) return 'success';
  if (status === 1) return 'warning';
  return 'danger'; // 0 或 3
};

const getStatusText = (status) => {
  if (status === 0) return '待开始';
  if (status === 1) return '识别中';
  if (status === 2) return '已完成';
  if (status === 3) return '失败';
  return '未知';
};

const getScoreType = (score) => {
  if (!score) return 'info';
  if (score >= 0.85) return 'success';
  if (score >= 0.70) return 'warning';
  return 'danger';
};

// 拉取数据
const fetchReports = async () => {
  loading.value = true;
  try {
    const res = await getList({});
    if (res.code === 200) {
      // 不再过滤 status === 2，展示所有
      reportList.value = res.data.sort((a, b) => b.taskId - a.taskId);
    }
  } catch (error) {
    ElMessage.error("获取报告列表失败");
  } finally {
    loading.value = false;
  }
};

// 前端搜索过滤
const filteredList = computed(() => {
  if (!searchKeyword.value) return reportList.value;
  const k = searchKeyword.value.toLowerCase();
  return reportList.value.filter(item =>
      String(item.taskId).includes(k) ||
      (item.fileName && item.fileName.toLowerCase().includes(k)) ||
      (item.taskName && item.taskName.toLowerCase().includes(k))
  );
});

// 查看详情
const viewDetail = (row) => {
  currentReport.value = row;
  dialogVisible.value = true;
};

// 导出 PDF
const exportPDF = async (row) => {
  try {
    ElMessage.info(`正在生成 [${row.fileName}] 的 PDF 报告，请稍候...`);

    // 调用 API
    const res = await exportReportPdf(row.taskId);

    // --- 通用文件下载逻辑 ---
    const blob = new Blob([res]); // 创建 blob 对象
    const fileName = `Report_${row.taskId}.pdf`;

    // 创建一个临时的 <a> 标签来触发下载
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);

    link.click(); // 触发点击

    // 清理
    document.body.removeChild(link);
    window.URL.revokeObjectURL(link.href);

    ElMessage.success("下载成功！");
  } catch (error) {
    console.error(error);
    ElMessage.error("导出失败，请检查服务器日志");
  }
};

onMounted(() => {
  fetchReports();
});
</script>

<style scoped>
.reports-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 84px);
}

.box-card {
  border-radius: 8px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.metrics-tags {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.text-gray {
  color: #909399;
  font-size: 12px;
}

.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 详情弹窗样式 */
.mb-20 {
  margin-bottom: 20px;
}

.score-text {
  font-weight: bold;
  color: #409EFF;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.image-grid {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.img-card {
  flex: 1;
  min-width: 280px;
  background: #f8f9fa;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  text-align: center;
}

.img-header {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
  font-size: 13px;
}

.detail-img {
  width: 100%;
  height: 260px;
  background: #fff;
  border-radius: 4px;
  object-fit: contain;
}

.img-err {
  height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 12px;
  background: #fff;
}
</style>