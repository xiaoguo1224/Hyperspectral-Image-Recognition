package org.example.server.controller;

import org.example.server.common.core.domain.AjaxResult;
import org.example.server.domain.HsiFile;
import org.example.server.service.impl.ReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/report")
public class ReportController {

    @Autowired
    ReportService reportService;

    @PostMapping("/cube")
    public AjaxResult cubeView(@RequestBody HsiFile hsiFile) {
        Map<String, Object> data = reportService.getCubeView(hsiFile.getStoragePath());
        if ((Integer) data.get("code") == 500) {
            return AjaxResult.error((String) data.get("msg"));
        }
        return AjaxResult.success("返回成功", data.get("data"));
    }
}
