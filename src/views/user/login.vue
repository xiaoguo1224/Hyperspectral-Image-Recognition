<template>
  <div class="login-container">
    <el-card class="login-box">
      <template #header>
        <h2 class="login-title">高光谱识别系统 - 登录</h2>
      </template>
      <el-form :model="loginForm" :rules="rules" ref="loginRef">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="学号/用户名" prefix-icon="User"/>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" show-password/>
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="handleLogin" class="submit-btn">登 录</el-button>
        <div class="footer-links">
          <router-link to="/register">注册账号</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive} from 'vue';
import {useRouter} from 'vue-router';
import {User, Lock} from '@element-plus/icons-vue';
import {ElMessage} from 'element-plus';

const router = useRouter();
const loading = ref(false);
const loginRef = ref(null);

const loginForm = reactive({
  username: '',
  password: ''
});

const rules = {
  username: [{required: true, message: '请输入学号', trigger: 'blur'}],
  password: [{required: true, message: '请输入密码', trigger: 'blur'}]
};

const handleLogin = () => {
  loginRef.value.validate((valid) => {
    if (valid) {
      loading.value = true;
      // 模拟登录成功，实际开发需调用 SpringBoot 的登录接口
      setTimeout(() => {
        localStorage.setItem('token', 'dummy-jwt-token');
        ElMessage.success('登录成功');
        router.push('/dashboard');
        loading.value = false;
      }, 1000);
    }
  });
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}

.login-box {
  width: 400px;
  border-radius: 8px;
}

.login-title {
  text-align: center;
  margin: 0;
  color: #303133;
}

.submit-btn {
  width: 100%;
  margin-top: 10px;
}

.footer-links {
  margin-top: 15px;
  text-align: right;
  font-size: 14px;
}
</style>