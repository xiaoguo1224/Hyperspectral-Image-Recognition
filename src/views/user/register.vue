<template>
  <div class="register-container">
    <el-card class="register-box">
      <template #header>
        <h2 class="register-title">新用户注册</h2>
      </template>
      <el-form :model="regForm" :rules="rules" ref="regRef" label-width="0px">
        <el-form-item prop="username">
          <el-input v-model="regForm.username" placeholder="请输入学号 (2022...)" prefix-icon="User"/>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="regForm.password" type="password" placeholder="设置密码" prefix-icon="Lock"/>
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="regForm.confirmPassword" type="password" placeholder="确认密码" prefix-icon="Check"/>
        </el-form-item>
        <el-button type="success" @click="handleRegister" class="submit-btn">立即注册</el-button>
        <div class="footer-links">
          已有账号？
          <router-link to="/predict">返回登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import {reactive, ref} from 'vue';
import {User, Lock, Check} from '@element-plus/icons-vue';
import {ElMessage} from 'element-plus';

const regRef = ref(null);
const regForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
});

const rules = {
  username: [{required: true, message: '学号不能为空', trigger: 'blur'}],
  password: [{required: true, min: 6, message: '密码至少6位', trigger: 'blur'}],
  confirmPassword: [{
    validator: (rule, value, callback) => {
      if (value !== regForm.password) callback(new Error('两次输入密码不一致'));
      else callback();
    },
    trigger: 'blur'
  }]
};

const handleRegister = () => {
  regRef.value.validate((valid) => {
    if (valid) ElMessage.success('注册成功，请登录');
  });
};
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.register-box {
  width: 400px;
}

.register-title {
  text-align: center;
  margin: 0;
}

.submit-btn {
  width: 100%;
}

.footer-links {
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}
</style>