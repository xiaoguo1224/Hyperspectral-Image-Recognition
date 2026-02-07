from flask import Flask, request, jsonify

app = Flask(__name__)
import os
# 假设这段代码是在 app.py 中运行的
from modules.DMSSNHyperspectral import DMSSNHyperspectral

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path_abs = os.path.join(BASE_DIR, 'static', 'DMSSN_double_epoch_100.pth')

# output_dir_abs = os.path.join(BASE_DIR, 'static', 'results')

output_dir_abs = "F:/Temp/uploadPath/output"

print(f"[DEBUG] Model Path: {model_path_abs}")
print(f"[DEBUG] Output Dir: {output_dir_abs}")

dmmsn_engine = DMSSNHyperspectral(
    model_path=model_path_abs,
    output_dir=output_dir_abs
)


@app.route('/predict', methods=['POST'])
def run_prediction():
    pic_list = request.json.get('pic_list')
    file_list = request.json.get('file_list')

    if not pic_list or not file_list:
        return jsonify({"error": "Missing input lists"}), 400

    errors, completed = dmmsn_engine.predict(pic_list, file_list)

    results_with_data = []
    for mask_url, mat_path in zip(completed, file_list):
        # 提取该 mat 文件的 200 波段数据
        spectral_data = dmmsn_engine.get_spectral_curve(mat_path)

        results_with_data.append({
            "mask_url": mask_url,
            "spectral_data": spectral_data,  # 这里传出 list
        })

    return jsonify({
        "status": "success",
        "completed_files": results_with_data,
        "failed_ids": errors
    })


@app.route('/evaluate', methods=['POST'])
def evaluate():
    pic_path = request.json.get('pic_path')
    gt_path = request.json.get('gt_path')
    dataMap = dmmsn_engine.evaluate(pic_path, gt_path)
    return jsonify({
        "status": "success",
        "data": dataMap
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
