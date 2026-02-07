package org.example.server.service;

import org.example.server.domain.DetectionTask;

public interface IPredictService {
    DetectionTask executePredict(DetectionTask task);

    DetectionTask executeEvaluate(DetectionTask task);
}