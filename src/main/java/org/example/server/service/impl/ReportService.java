package org.example.server.service.impl;

import org.example.server.common.config.Config;
import org.example.server.common.config.ServerConfig;
import org.example.server.service.IReportService;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class ReportService implements IReportService {
    @Override
    public Map<String, Object> getCubeView(String matPath) {

        String absoluteMatPath = Config.getabsolutePath(matPath);
        Map<String, Object> request = new HashMap<>();
        request.put("path", absoluteMatPath);
        return ServerConfig.getResponse("/visual/cube-heavy", request);
    }
}
