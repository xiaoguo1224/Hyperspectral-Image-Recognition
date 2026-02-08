package org.example.server.service.impl;

import com.alibaba.fastjson.JSON;
import org.example.server.common.config.Config;
import org.example.server.common.config.ServerConfig;
import org.example.server.domain.DetectionTask;
import org.example.server.mapper.DetectionTaskMapper;
import org.example.server.service.IPredictService;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.List;

@Service
public class PredictServiceImpl implements IPredictService {


    @Autowired
    private DetectionTaskMapper taskMapper;


    @Override
    public DetectionTask executePredict(DetectionTask task) {
        task.setStatus(1); // 识别中
        taskMapper.updateById(task);

        String absoluteJpg = Config.getabsolutePath(task.getJpgFile().getStoragePath());
        String absoluteMat = Config.getabsolutePath(task.getMatFile().getStoragePath());

        Map<String, Object> request = new HashMap<>();
        request.put("pic_list", new String[]{absoluteJpg});
        request.put("file_list", new String[]{absoluteMat});
        try {
            Map<String, Object> response = ServerConfig.getResponse("/predict", request);

            List<Map<String, Object>> completed = (List<Map<String, Object>>) response.get("completed_files");

            if (completed != null && !completed.isEmpty()) {
                Map<String, Object> resultEntry = completed.get(0);

                // 1. 处理并转换 Mask 路径
                String rawMaskPath = (String) resultEntry.get("mask_url");
                String processedMaskPath = Config.formatPath(rawMaskPath);

                // 2. 处理光谱特征曲线数据 (200波段数据)
                // Python 传回的是 List<Double>，存入数据库需要转为 JSON 字符串
                Object spectralDataObj = resultEntry.get("spectral_data");
                if (spectralDataObj != null) {
                    task.setSpectralData(JSON.toJSONString(spectralDataObj));
                }

                task.setStatus(2); // 完成
                task.setMaskPath(processedMaskPath);
            }
            taskMapper.updateById(task);
        } catch (Exception e) {
            e.printStackTrace();
            task.setStatus(3); // 识别失败
            taskMapper.updateById(task);
        }
        return task;
    }

    @Override
    public DetectionTask executeEvaluate(DetectionTask task) {

        //获取绝对路径
        String absolutePred = Config.getabsolutePath(task.getMaskPath());
        String absoluteGt = Config.getabsolutePath(task.getGtFile().getStoragePath());

        Map<String, Object> request = new HashMap<>();
        request.put("pic_path", absolutePred);
        request.put("gt_path", absoluteGt);

        Map<String, Object> response = ServerConfig.getResponse("/evaluate", request);
        Map<String, Double> data = (Map<String, Double>) response.get("data");
        task.setF1(data.get("f1"));
        task.setMae(data.get("mae"));
        task.setPred(data.get("pred"));
        task.setRec(data.get("rec"));
        task.setAuc(data.get("auc"));
        task.setCc(data.get("cc"));
        task.setNss(data.get("nss"));
        taskMapper.updateById(task);

        return task;

    }

}