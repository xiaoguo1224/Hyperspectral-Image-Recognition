<template>
  <div class="reports">
    <el-card header="历史识别报告记录">
      <el-table :data="reportList">
        <el-table-column prop="jobId" label="任务编号" width="180"/>
        <el-table-column prop="fileName" label="源数据立方体"/>
        <el-table-column prop="model" label="所用算法"/>
        <el-table-column label="识别精度">
          <template #default="scope">
            <el-tag :type="scope.row.mAP > 0.75 ? 'success' : 'info'">
              mAP: {{ scope.row.mAP }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="报告导出">
          <template #default="scope">
            <el-button type="primary" size="small" @click="exportPDF(scope.row)">
              导出 PDF 报告
            </el-button>
            <el-button size="small" @click="viewDetail(scope.row)">查看大图</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import {ref} from 'vue';
import {ElMessage} from 'element-plus';

const reportList = ref([
  {jobId: 'TASK-20260205-01', fileName: 'scene_01.mat', model: 'ACEN', mAP: 0.79},
  {jobId: 'TASK-20260205-02', fileName: 'scene_05.mat', model: 'YOLOv8s', mAP: 0.76},
  {jobId: 'TASK-20260201-08', fileName: 'complex_bg.mat', model: 'RX', mAP: 0.58}
]);

const exportPDF = (row) => {
  ElMessage.success(`正在生成任务 ${row.jobId} 的详细检测报告...`);
  // 实际开发中，这里可以调用 SpringBoot 的接口返回文件流，或者前端使用 jsPDF 库生成
};

const viewDetail = (row) => {
  // 跳转回推理页面或打开 Modal 展示详细像素级检测图
};
</script>