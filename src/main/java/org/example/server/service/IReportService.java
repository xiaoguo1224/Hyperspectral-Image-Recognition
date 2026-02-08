package org.example.server.service;

import java.util.Map;

public interface IReportService {

    Map<String,Object> getCubeView(String matPath);
}
