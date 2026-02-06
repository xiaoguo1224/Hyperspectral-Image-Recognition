from flask import Flask, request, jsonify

from modules.inference_module import HyperspectralInference

app = Flask(__name__)
import os
# 假设这段代码是在 app.py 中运行的
from modules.inference_module import HyperspectralInference  # 根据你的目录结构导入

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path_abs = os.path.join(BASE_DIR, 'static', 'DMSSN_double_epoch_100.pth')

# output_dir_abs = os.path.join(BASE_DIR, 'static', 'results')

output_dir_abs = "F:/Temp/uploadPath/output"

print(f"[DEBUG] Model Path: {model_path_abs}")
print(f"[DEBUG] Output Dir: {output_dir_abs}")

infer_engine = HyperspectralInference(
    model_path=model_path_abs,
    output_dir=output_dir_abs
)


@app.route('/predict', methods=['POST'])
def run_prediction():
    pic_list = request.json.get('pic_list')
    file_list = request.json.get('file_list')

    if not pic_list or not file_list:
        return jsonify({"error": "Missing input lists"}), 400

    errors, completed = infer_engine.predict(pic_list, file_list)

    return jsonify({
        "status": "success",
        "completed_files": completed,
        "failed_ids": errors
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
