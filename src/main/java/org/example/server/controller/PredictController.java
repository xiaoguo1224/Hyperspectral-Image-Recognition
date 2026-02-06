package org.example.server.controller;

import org.example.server.common.core.domain.AjaxResult;
import org.example.server.domain.DetectionTask;
import org.example.server.service.IPredictService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/detection")
public class PredictController {

    private final IPredictService predictService;

    public PredictController(IPredictService predictService) {
        this.predictService = predictService;
    }

    @PostMapping("/predict")
    public AjaxResult runPredict(@RequestBody Map<String, Long> params) {
        Long matId = params.get("matFileId");
        Long jpgId = params.get("jpgFileId");

        DetectionTask task = predictService.executePredict(matId, jpgId);
        return AjaxResult.success("预测成功", task);
    }
}