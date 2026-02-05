from flask import Flask, request, jsonify

from modules.inference_module import HyperspectralInference

app = Flask(__name__)

# 全局初始化，模型只加载一次
infer_engine = HyperspectralInference(
    model_path='../outputs/DMSSN_double_epoch_100.pth',
    output_dir='../static/results/'
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
