# Model Module - 高光谱图像识别模型

## 概述

本模块包含高光谱图像识别的核心深度学习模型和算法。

## 目录结构

```
model/
├── app.py                 # 主应用程序入口
├── assistant/            # 辅助工具
│   ├── dataloader.py    # 数据加载器
│   ├── data_aug.py      # 数据增强
│   └── sc_norm.py       # 标准化处理
├── models/               # 模型定义
│   ├── DSST.py          # DSST 模型
│   └── evaluate_function.py  # 评估函数
└── modules/              # 模块组件
    ├── DMSSNHyperspectral.py  # 高光谱模块
    └── VisualController.py    # 可视化控制器
```

## 功能特性

- ✅ DSST 高光谱图像分类模型
- ✅ 数据增强和预处理
- ✅ 模型评估和验证
- ✅ 可视化分析

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 训练模型

```bash
python app.py --train --data_path /path/to/data
```

### 推理预测

```bash
python app.py --predict --model_path /path/to/model --input_path /path/to/input
```

## 主要组件

### DSST 模型

DSST (Deep Spectral-Spatial Transformer) 是一个用于高光谱图像分类的深度学习模型。

### 数据增强

提供多种数据增强方法：
- 随机旋转
- 翻转
- 色彩变换
- 噪声注入

### 评估函数

包含常用的评估指标：
- 总体精度 (OA)
- 平均精度 (AA)
- Kappa 系数
- 混淆矩阵

## 技术栈

- Python 3.8+
- PyTorch
- NumPy
- OpenCV
- Matplotlib

## 相关分支

- 主分支：[master](../tree/master)
- RAG 模块：[branch-rag](../tree/branch-rag)
- 服务器模块：[branch-server](../tree/branch-server)
- Web 前端：[branch-web](../tree/branch-web)

## 许可证

本项目用于毕业设计目的
