import numpy as np
import scipy.io as sio
from flask import jsonify, request


# 针对 512x512x200 数据的专用处理函数
def get_optimized_cube_data(mat_path):
    try:
        data_map = sio.loadmat(mat_path)
        # 自动查找数据 Key
        key = [k for k in data_map.keys() if not k.startswith('__')][0]
        cube = data_map[key]

        # 统一维度顺序: [H, W, Bands] -> [512, 512, 200]
        # 如果你的数据是 [200, 512, 512]，需要转置
        if cube.shape[0] == 200:
            cube = np.transpose(cube, (1, 2, 0))  # 变为 [512, 512, 200]

        H, W, B = cube.shape

        # --- 核心优化策略 ---
        # 目标：将 5200万个点 压缩到 约 30万个点 (Web渲染的甜蜜点)
        # 采样步长计算： (52000000 / 300000)^(1/3) ≈ 5.5
        # 我们取 5 或 6 的步长
        step = 6

        # 1. 降采样
        # 空间维(X,Y)步长为6，光谱维(Z)步长为2 (光谱特征更重要，少删一点)
        small_cube = cube[::step, ::step, ::2]

        # 2. 坐标网格生成 (对应原始坐标)
        x_indices = np.arange(0, W, step)
        y_indices = np.arange(0, H, step)
        z_indices = np.arange(0, B, 2)

        # 生成网格
        # 注意：ThreeJS中，通常 X/Z 是水平面(空间)，Y 是高度(光谱)
        # 但为了逻辑直观，我们这里：X=空间宽, Y=空间高, Z=光谱深
        xx, yy, zz = np.meshgrid(x_indices, y_indices, z_indices, indexing='ij')

        # 3. 展平数组
        flat_x = xx.flatten()
        flat_y = yy.flatten()
        flat_z = zz.flatten()
        flat_v = small_cube.flatten()

        # 4. 阈值过滤 (去背景) - 这一步对于"尽可能展现"很重要
        # 假设预处理后的数据，背景接近0。我们只保留有意义的点。
        threshold = np.mean(flat_v) * 0.1  # 动态阈值，过滤掉低于均值10%的噪点
        mask = flat_v > threshold

        # 应用过滤
        final_x = flat_x[mask]
        final_y = flat_y[mask]
        final_z = flat_z[mask]
        final_v = flat_v[mask]

        # 5. 归一化强度值 (用于前端上色)
        v_min, v_max = np.min(final_v), np.max(final_v)
        final_v_norm = (final_v - v_min) / (v_max - v_min + 1e-5)

        # 6. 组装返回数据
        # 为了传输快，我们不发对象列表，发平行数组
        return {
            "x": final_x.tolist(),
            "y": final_y.tolist(),
            "z": final_z.tolist(),
            "v": final_v_norm.tolist(),
            "bounds": [W, H, B]  # 原始尺寸
        }

    except Exception as e:
        print(f"Cube gen error: {e}")
        return None
