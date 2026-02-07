package org.example.server.service.impl;

import com.alibaba.fastjson.JSON;
import org.example.server.common.config.Config;
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

    @Value("${predict.url}")
    private String pythonUrl;


    @Autowired
    private DetectionTaskMapper taskMapper;

    private final RestTemplate restTemplate = new RestTemplate();


    @Override
    public DetectionTask executePredict(DetectionTask task) {
        task.setStatus(1); // 识别中
        taskMapper.updateById(task);

        // 获取数据库存储路径并转换为正斜杠格式，确保匹配一致性
        String dbJpgPath = task.getJpgFile().getStoragePath().replace("\\", "/");
        String dbMatPath = task.getMatFile().getStoragePath().replace("\\", "/");

        // 转换为绝对路径传给 Flask
        String profilePath = Config.getProfile().replace("\\", "/");
        String absoluteJpg = profilePath + dbJpgPath.substring("/profile".length());
        String absoluteMat = profilePath + dbMatPath.substring("/profile".length());

        Map<String, Object> request = new HashMap<>();
        request.put("pic_list", new String[]{absoluteJpg});
        request.put("file_list", new String[]{absoluteMat});
        try {
            Map<String, Object> response = getResponse("/predict", request);

            List<Map<String, Object>> completed = (List<Map<String, Object>>) response.get("completed_files");

            if (completed != null && !completed.isEmpty()) {
                Map<String, Object> resultEntry = completed.get(0);

                // 1. 处理并转换 Mask 路径
                String rawMaskPath = (String) resultEntry.get("mask_url");
                String processedMaskPath = formatPath(rawMaskPath);

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
        // 获取数据库存储路径并转换为正斜杠格式，确保匹配一致性
        String dbPredPath = task.getMaskPath().replace("\\", "/");
        String dbGtPath = task.getGtFile().getStoragePath().replace("\\", "/");

        // 转换为绝对路径传给 Flask
        String profilePath = Config.getProfile().replace("\\", "/");
        String absolutePred = profilePath + dbPredPath.substring("/profile".length());
        String absoluteGt = profilePath + dbGtPath.substring("/profile".length());

        Map<String, Object> request = new HashMap<>();
        request.put("pic_path", absolutePred);
        request.put("gt_path", absoluteGt);

        Map<String, Object> response = getResponse("/evaluate", request);
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

    private Map<String, Object> getResponse(String pythonApi, Map<String, Object> request) {

        String fullUrl = pythonUrl + pythonApi;
        try {
            Map<String, Object> response = restTemplate.postForObject(fullUrl, request, Map.class);
            if (response != null && "success".equals(response.get("status"))) {
                return response;
            }
        } catch (Exception e) {
            throw new RuntimeException();
        }
        return null;
    }


    /**
     * 统一路径处理逻辑：绝对路径 -> /profile 相对路径，并统一斜杠
     */
    private String formatPath(String rawAbsolutePath) {
        if (rawAbsolutePath == null) return null;

        // 统一为正斜杠
        String absolutePath = rawAbsolutePath.replace("\\", "/");
        String profileRoot = Config.getProfile().replace("\\", "/");

        String relativePath = "";
        if (absolutePath.contains(profileRoot)) {
            relativePath = absolutePath.substring(profileRoot.length());
        } else {
            relativePath = absolutePath;
        }

        // 确保以 / 开头并拼接前缀
        if (!relativePath.startsWith("/")) {
            relativePath = "/" + relativePath;
        }
        return "/profile" + relativePath;
    }
}