package org.example.server.service.impl;

import org.example.server.domain.DetectionTask;
import org.example.server.mapper.DetectionTaskMapper;
import org.example.server.service.IPredictService;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
public class PredictServiceImpl implements IPredictService {

    @Value("${predict.url}")
    private String pythonUrl;

    @Value("${predict.api}")
    private String pythonApi;

    private final DetectionTaskMapper taskMapper;
    private final RestTemplate restTemplate = new RestTemplate();

    public PredictServiceImpl(DetectionTaskMapper taskMapper) {
        this.taskMapper = taskMapper;
    }

    @Override
    public DetectionTask executePredict(Long matFileId, Long jpgFileId) {
        // 1. 初始化任务记录
        DetectionTask task = new DetectionTask();
        task.setMatFileId(matFileId);
        task.setJpgFileId(jpgFileId);
        task.setStatus(1); // 识别中
        taskMapper.insert(task);

        // 2. 封装请求数据给 Flask
        Map<String, Object> request = new HashMap<>();
        // 实际开发中应根据 FileId 查询真实物理路径传给 Flask
        request.put("pic_list", new String[]{"/data/pic/sample.jpg"});
        request.put("file_list", new String[]{"/data/mat/sample.mat"});

        try {
            // 3. 调用 Python 接口
            String fullUrl = pythonUrl + pythonApi;
            Map<String, Object> response = restTemplate.postForObject(fullUrl, request, Map.class);

            // 4. 解析结果并更新数据库
            if (response != null && "success".equals(response.get("status"))) {
                task.setStatus(2);
                task.setMaskPath((String) response.get("mask_url"));
                task.setMapValue(0.785); // 模拟返回，实际应从 response 获取
                task.setF1Score(0.72);
                taskMapper.updateById(task);
            }
        } catch (Exception e) {
            task.setStatus(3); // 失败
            taskMapper.updateById(task);
        }
        return task;
    }
}