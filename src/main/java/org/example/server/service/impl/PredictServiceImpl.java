package org.example.server.service.impl;

import org.example.server.common.config.Config;
import org.example.server.domain.DetectionTask;
import org.example.server.mapper.DetectionTaskMapper;
import org.example.server.service.IPredictService;
import org.jspecify.annotations.Nullable;
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

    @Value("${predict.api}")
    private String pythonApi;

    private final DetectionTaskMapper taskMapper;
    private final RestTemplate restTemplate = new RestTemplate();

    public PredictServiceImpl(DetectionTaskMapper taskMapper) {
        this.taskMapper = taskMapper;
    }

    @Override
    public DetectionTask executePredict(DetectionTask task) {
        task.setStatus(1);
        taskMapper.updateById(task);

        String dbJpgPath = task.getJpgFile().getStoragePath();
        String dbMatPath = task.getMatFile().getStoragePath();

        // 转换为绝对路径传给 Flask
        // 先去掉开头的 /profile，再拼接物理根目录
        String absoluteJpg = Config.getProfile() + dbJpgPath.substring("/profile".length());
        String absoluteMat = Config.getProfile() + dbMatPath.substring("/profile".length());

        Map<String, Object> request = new HashMap<>();
        request.put("pic_list", new String[]{absoluteJpg});
        request.put("file_list", new String[]{absoluteMat});

        try {
            // 3. 调用 Flask 接口
            String fullUrl = pythonUrl + pythonApi;
            Map<String, Object> response = restTemplate.postForObject(fullUrl, request, Map.class);
            System.out.println(response);
            // 4. 解析结果并更新数据库
            if (response != null && "success".equals(response.get("status"))) {
                List<String> completed = (List<String>) response.get("completed_files");

                if (completed != null && !completed.isEmpty()) {

                    // 获取 Python 返回的绝对路径，例如 F:/Temp/uploadPath/output/result_xxx.png
                    String relativeMaskPath = getString(completed);

                    task.setStatus(2); // 完成
                    task.setMaskPath(relativeMaskPath);

                }
                taskMapper.updateById(task);
            }
        } catch (Exception e) {
            e.printStackTrace();
            task.setStatus(3); // 识别失败
            taskMapper.updateById(task);
        }
        return task;
    }

    private static @Nullable String getString(List<String> completed) {
        if (completed == null || completed.isEmpty()) return null;
        String rawAbsolutePath = (String) completed.get(0);
        String absoluteMaskPath = rawAbsolutePath.replace("\\", "/");
        String profileRoot = Config.getProfile().replace("\\", "/");
        String relativeMaskPath = "";
        if (absoluteMaskPath != null && absoluteMaskPath.contains(profileRoot)) {
            relativeMaskPath = absoluteMaskPath.substring(profileRoot.length());
        } else {
            relativeMaskPath = absoluteMaskPath; // 容错处理
        }

        // 拼接数据库映射前缀，并确保返回的路径以单个 / 开头
        if (!relativeMaskPath.startsWith("/")) {
            relativeMaskPath = "/" + relativeMaskPath;
        }

        return "/profile" + relativeMaskPath;
    }
}