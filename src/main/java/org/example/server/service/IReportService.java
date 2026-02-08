package org.example.server.service;

import jakarta.servlet.http.HttpServletResponse;
import org.example.server.domain.DetectionTask;

import java.util.Map;

public interface IReportService {

    Map<String, Object> getCubeView(String matPath);

    void exportPdf(DetectionTask task, HttpServletResponse response);
}
