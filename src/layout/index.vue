<template>
  <el-container class="layout-container">
    <el-aside width="240px" class="aside">
      <div class="logo">
        <el-icon :size="24" color="#409EFF">
          <Platform/>
        </el-icon>
        <span>高光谱检测系统</span>
      </div>

      <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
      >
        <el-menu-item index="/dashboard">
          <el-icon>
            <Histogram/>
          </el-icon>
          <span>系统概览</span>
        </el-menu-item>

        <el-menu-item index="/detection/index">
          <el-icon>
            <Aim/>
          </el-icon>
          <span>目标检测识别</span>
        </el-menu-item>
        <el-menu-item index="/evaluation/index">
          <el-icon>
            <Search/>
          </el-icon>
          <span>结果评估</span>
        </el-menu-item>

        <el-menu-item index="/spectral/library">
          <el-icon>
            <Collection/>
          </el-icon>
          <span>光谱特征库</span>
        </el-menu-item>


        <el-menu-item index="/rag/index">
          <el-icon>
            <ChatRound/>
          </el-icon>
          <span>智能检索问答</span>
        </el-menu-item>

        <el-menu-item index="/reports/index">
          <el-icon>
            <Document/>
          </el-icon>
          <span>检测报告管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRouteTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component"/>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {computed} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {
  Platform, Histogram, Search, Collection,
  Document, ArrowDown,ChatRound
} from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();

// 计算当前激活的菜单项
const activeMenu = computed(() => {
  return route.path;
});

// 获取当前路由的面包屑标题
const currentRouteTitle = computed(() => {
  return route.meta.title || '控制台';
});

</script>

<style scoped>
.layout-container {
  height: 98vh;
  width: 99vw;
}

.aside {
  background-color: #304156;
  color: #fff;
  transition: width 0.3s;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: bold;
  font-size: 18px;
  background: #2b2f3a;
}

.el-menu-vertical {
  border-right: none;
}

.header {
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>