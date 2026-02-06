<template>
  <div class="upload-file">
    <el-upload
        ref="fileUploadRef"
        multiple
        :action="uploadFileUrl"
        :before-upload="handleBeforeUpload"
        :file-list="fileList"
        :limit="limit"
        :on-error="handleUploadError"
        :on-exceed="handleExceed"
        :on-success="handleUploadSuccess"
        :show-file-list="false"
        :headers="headers"
        name="files"
        class="upload-file-uploader"
    >
      <el-button type="primary">选取文件</el-button>

      <template #tip v-if="showTip">
        <div class="el-upload__tip">
          请上传
          <template v-if="fileSize"> 大小不超过 <b style="color: #f56c6c">{{ fileSize }}MB</b></template>
          <template v-if="fileType"> 格式为 <b style="color: #f56c6c">{{ fileType.join('/') }}</b></template>
          的文件
        </div>
      </template>
    </el-upload>

    <transition-group class="upload-file-list el-upload-list el-upload-list--text" name="el-fade-in-linear" tag="ul">
      <li :key="file.uid || file.url" class="el-upload-list__item ele-upload-list__item-content"
          v-for="(file, index) in fileList">
        <el-link :href="`${baseUrl}${file.url}`" :underline="false" target="_blank">
          <span class="el-icon-document"> {{ getFileName(file.name) }} </span>
        </el-link>
        <div class="ele-upload-list__item-content-action">
          <el-link :underline="false" @click="handleDelete(index)" type="danger">删除</el-link>
        </div>
      </li>
    </transition-group>
  </div>
</template>

<script setup>
import {ref, computed, watch} from 'vue'
import {ElMessage, ElLoading} from 'element-plus'

const props = defineProps({
  // 值 (逗号分隔的相对路径字符串，例如 "/profile/upload/1.png,/profile/upload/2.png")
  modelValue: {
    type: [String, Object, Array],
    default: () => []
  },
  // 数量限制
  limit: {
    type: Number,
    default: 5
  },
  // 大小限制(MB)
  fileSize: {
    type: Number,
    default: 5
  },
  // 文件类型
  fileType: {
    type: Array,
    default: () => ['doc', 'xls', 'ppt', 'txt', 'pdf', 'docx', 'xlsx', 'pptx', 'mp3', 'mp4', 'zip', 'rar', 'jpg', 'png']
  },
  // 是否显示提示
  isShowTip: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

// 变量定义
const number = ref(0)
const uploadList = ref([])
// 这里的 VITE_APP_BASE_API 对应后端服务地址前缀，例如 "http://localhost:8080"
const baseUrl = import.meta.env.VITE_APP_BASE_API
// 修改接口地址为 /common/uploads
const uploadFileUrl = ref(import.meta.env.VITE_APP_BASE_API + '/common/uploads')
const fileList = ref([])
const fileUploadRef = ref(null)
const loadingInstance = ref(null)
// 如果你需要设置 headers (例如 token)，可以在这里定义，通常从 store 或 cookie 获取
const headers = ref({
  // Authorization: 'Bearer ' + getToken()
})

// 计算属性：是否显示提示
const showTip = computed(() => {
  return props.isShowTip && (props.fileType || props.fileSize)
})

// // 监听 modelValue 变化，回显数据
// watch(() => props.modelValue, (val) => {
//   if (val) {
//     let temp = 1
//     // 首先将值转为数组
//     const list = Array.isArray(val) ? val : val.split(',')
//     // 然后将数组转为对象数组
//     fileList.value = list.map(item => {
//       if (typeof item === 'string') {
//         // 回显时，name 和 url 暂时都设为路径，具体文件名由 getFileName 处理
//         item = {name: item, url: item}
//       }
//       // 添加uid防止key重复
//       item.uid = item.uid || new Date().getTime() + temp++
//       return item
//     })
//   } else {
//     fileList.value = []
//   }
// }, {deep: true, immediate: true})

// 方法

// 获取文件名称 (处理路径字符串)
const getFileName = (name) => {
  if (name && name.lastIndexOf('/') > -1) {
    return name.slice(name.lastIndexOf('/') + 1)
  } else {
    return name
  }
}

// 上传前校检格式和大小
const handleBeforeUpload = (file) => {
  // 校检文件类型
  if (props.fileType) {
    const fileName = file.name.split('.')
    const fileExt = fileName[fileName.length - 1]
    const isTypeOk = props.fileType.indexOf(fileExt) >= 0
    if (!isTypeOk) {
      ElMessage.error(`文件格式不正确, 请上传${props.fileType.join('/')}格式文件!`)
      return false
    }
  }
  // 校检文件大小
  if (props.fileSize) {
    const isLt = file.size / 1024 / 1024 < props.fileSize
    if (!isLt) {
      ElMessage.error(`上传文件大小不能超过 ${props.fileSize} MB!`)
      return false
    }
  }

  // 开启 Loading
  loadingInstance.value = ElLoading.service({
    text: '正在上传文件，请稍候...',
    background: 'rgba(0, 0, 0, 0.7)',
  })

  number.value++
  return true
}

// 文件个数超出
const handleExceed = () => {
  ElMessage.error(`上传文件数量不能超过 ${props.limit} 个!`)
}

// 上传失败
const handleUploadError = (err) => {
  ElMessage.error('上传文件失败，请重试')
  if (loadingInstance.value) loadingInstance.value.close()
  number.value--
}

// 上传成功回调
const handleUploadSuccess = (res, file) => {
  if (res.code === 200) {
    // 后端返回的是逗号分隔的字符串：
    // res.fileNames -> 相对路径 (用于保存到数据库)
    // res.originalFilenames -> 原始文件名 (用于展示)
    // res.urls -> 完整URL

    // 虽然 el-upload 默认一次发送一个文件，但后端接口逻辑是通用的
    // 我们这里按照后端逻辑解析逗号分隔符，以防未来改为并发批量上传
    const relativePaths = res.fileNames ? res.fileNames.split(',') : [];
    const originalNames = res.originalFilenames ? res.originalFilenames.split(',') : [];

    relativePaths.forEach((path, index) => {
      uploadList.value.push({
        name: originalNames[index] || path, // 优先显示原始文件名
        url: path
      })
    });

    uploadedSuccessfully()
  } else {
    number.value--
    if (loadingInstance.value) loadingInstance.value.close()
    ElMessage.error(res.msg)
    // 移除上传失败的文件
    fileUploadRef.value?.handleRemove(file)
  }
}

// 删除文件
const handleDelete = (index) => {
  fileList.value.splice(index, 1)
  emit('update:modelValue', listToString(fileList.value))
}

// 上传结束处理
const uploadedSuccessfully = () => {
  if (number.value > 0 && uploadList.value.length === number.value) {
    fileList.value = fileList.value.concat(uploadList.value)
    uploadList.value = []
    number.value = 0
    // 将文件列表转为逗号分隔的字符串传给父组件
    emit('update:modelValue', listToString(fileList.value))
    if (loadingInstance.value) loadingInstance.value.close()
  }
}

// 对象转成指定字符串分隔
const listToString = (list, separator) => {
  let strs = ''
  separator = separator || ','
  for (let i in list) {
    // 兼容可能存在的 undefined url
    if (list[i].url) {
      strs += list[i].url + separator
    }
  }
  return strs !== '' ? strs.substr(0, strs.length - 1) : ''
}
</script>

<style scoped>
.upload-file-uploader {
  margin-bottom: 5px;
}

.upload-file-list .el-upload-list__item {
  border: 1px solid #e4e7ed;
  line-height: 2;
  margin-bottom: 10px;
  position: relative;
}

.upload-file-list .ele-upload-list__item-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: inherit;
}

.ele-upload-list__item-content-action .el-link {
  margin-right: 10px;
}
</style>