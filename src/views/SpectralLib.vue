<template>
  <div class="spectral-lib">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>HSOD-BIT 特征光谱库</span>
          <el-button type="primary" size="small">新增特征端元</el-button>
        </div>
      </template>

      <el-table :data="libData" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80"/>
        <el-table-column prop="name" label="目标类别"/>
        <el-table-column label="光谱曲线预览" width="300">
          <template #default="scope">
            <div :id="'mini-chart-' + scope.$index" style="height: 60px; width: 260px;"></div>
          </template>
        </el-table-column>
        <el-table-column prop="updateTime" label="录入时间"/>
        <el-table-column label="操作">
          <template #default>
            <el-button link type="primary">详细波段数据</el-button>
            <el-button link type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import {ref, onMounted, nextTick} from 'vue';
import * as echarts from 'echarts';

const libData = [
  {id: 'S001', name: '金属目标 (疑似)', updateTime: '2026-01-10'},
  {id: 'S002', name: '绿色植被 (背景)', updateTime: '2026-01-12'},
  {id: 'S003', name: '伪装网 (干扰)', updateTime: '2026-01-15'}
];

onMounted(() => {
  // 模拟为表格每一行渲染微缩图
  nextTick(() => {
    libData.forEach((item, index) => {
      const chart = echarts.init(document.getElementById(`mini-chart-${index}`));
      chart.setOption({
        grid: {top: 5, bottom: 5, left: 5, right: 5},
        xAxis: {type: 'category', show: false},
        yAxis: {type: 'value', show: false},
        series: [{
          data: Array.from({length: 20}, () => Math.random()),
          type: 'line',
          smooth: true,
          areaStyle: {opacity: 0.2},
          symbol: 'none'
        }]
      });
    });
  });
});
</script>