import os
import glob
import torch
import warnings
from torch.utils.data import DataLoader
from torchvision import utils
# 确保导入路径正确，根据你的 Flask 目录结构调整
from assistant.dataloader import HL_SC
from models.DSST import ACEN


class HyperspectralInference:
    def __init__(self, model_path='/static/DMSSN_double_epoch_100.pth', output_dir='/static/results/'):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.output_dir = output_dir
        self.model_path = model_path

        # 预加载模型
        self.model = ACEN()
        self._load_model()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _load_model(self):
        print(f"[INFO] Loading model on {self.device}...")
        self.model.to(self.device)
        # map_location 确保在没有 GPU 的机器上也能加载 GPU 训练的模型
        checkpoint = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint, strict=False)
        self.model.eval()
        print("[INFO] Model loaded and set to eval mode")

    def _data_process(self, pic_list, file_list, batch_size):
        test_dataset = HL_SC(img_list=pic_list, file_list=file_list)
        return DataLoader(test_dataset, batch_size=batch_size, num_workers=0, drop_last=False)

    def _save_image_tensor(self, input_tensor: torch.Tensor, filename):
        # 归一化并保存
        input_tensor = input_tensor.clone().detach().cpu()
        input_tensor = (input_tensor - torch.min(input_tensor)) / (torch.max(input_tensor) - torch.min(input_tensor))
        # 调整维度以符合 torchvision 要求 [C, H, W]
        input_tensor = torch.swapaxes(input_tensor, 2, 1)
        utils.save_image(input_tensor, filename)

    def predict(self, pic_list, file_list, batch_size=6):
        test_loader = self._data_process(pic_list, file_list, batch_size)
        complete_file_list = []
        error_list = []

        with torch.no_grad():
            for data in test_loader:
                inputs, names = data['image'], data['id']
                inputs_v = inputs.to(self.device)

                # 解包模型输出，根据原代码取第五个返回值 out
                _, _, _, _, out = self.model(inputs_v)

                # 获取当前 batch 的实际大小，防止最后不满一整包报错
                current_batch_size = out.size(0)
                for j in range(current_batch_size):
                    img_id = names[j]
                    try:
                        draw = out[j, :, :, :]
                        save_path = os.path.join(self.output_dir, f"{img_id}.jpg")
                        self._save_image_tensor(draw, save_path)
                        complete_file_list.append(save_path)
                    except Exception as e:
                        print(f"Error processing {img_id}: {e}")
                        error_list.append(img_id)

        return error_list, complete_file_list


if __name__ == '__main__':
    # 全局初始化，模型只加载一次
    infer_engine = HyperspectralInference(
        model_path='/static/DMSSN_double_epoch_100.pth',
        output_dir='/static/results/'
    )
