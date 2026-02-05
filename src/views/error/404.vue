<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code">404</h1>
      <p class="error-msg">抱歉，您访问的高光谱波段（页面）不存在或已丢失。</p>
      <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  background: #f0f2f5;
}

.error-code {
  font-size: 120px;
  color: #409EFF;
  margin: 0;
}

.error-msg {
  font-size: 20px;
  color: #606266;
  margin: 20px 0 30px;
}
</style>