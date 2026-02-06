<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code" style="color: #F56C6C;">401</h1>
      <p class="error-msg">身份认证失效，请重新登录系统。</p>
      <el-button type="danger" @click="$router.push('/predict')">去登录</el-button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fdf6f6;
}

.error-code {
  font-size: 120px;
  margin: 0;
}

.error-msg {
  font-size: 20px;
  margin: 20px 0 30px;
}
</style>