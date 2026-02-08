package org.example.server.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.example.server.common.core.domain.AjaxResult;
import org.example.server.domain.DetectionTask;
import org.example.server.domain.HsiFile;
import org.example.server.mapper.DetectionTaskMapper;
import org.example.server.mapper.HsiFileMapper;
import org.example.server.service.IPredictService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/detection")
public class PredictController {

    private final IPredictService predictService;
    @Autowired
    DetectionTaskMapper detectionTaskMapper;

    @Autowired
    HsiFileMapper hsiFileMapper;

    public PredictController(IPredictService predictService) {
        this.predictService = predictService;
    }

    @PostMapping("/predict")
    public AjaxResult runPredict(@RequestBody Map<String, Object> params) {

        String name = params.get("name").toString();
        DetectionTask task = detectionTaskMapper.selectOne(new LambdaQueryWrapper<DetectionTask>().eq(DetectionTask::getTaskName, name));

        String jpgPath = params.get("jpgUrl").toString();
        String matPath = params.get("matPath").toString();

        HsiFile matFile = hsiFileMapper.selectOne(new LambdaQueryWrapper<HsiFile>().eq(HsiFile::getStoragePath, matPath));
        HsiFile jpgFile = hsiFileMapper.selectOne(new LambdaQueryWrapper<HsiFile>().eq(HsiFile::getStoragePath, jpgPath));

        if (task != null) {
            if (task.getStatus() == 2) {
                return AjaxResult.success("预测成功", task);
            }
            task.setMatFile(matFile);
            task.setJpgFile(jpgFile);
        } else {
            task = new DetectionTask();
            task.setCreateTime(LocalDateTime.now());
            task.setTaskName(name);
            task.setMatFileId(matFile.getFileId());
            task.setJpgFileId(jpgFile.getFileId());
            task.setMatFile(matFile);
            task.setJpgFile(jpgFile);
            detectionTaskMapper.insert(task);
        }
        task = predictService.executePredict(task);
        if (task.getStatus() == 2) {
            return AjaxResult.success("预测成功", task);
        } else {
            return AjaxResult.error("失败", task);
        }

    }

    @GetMapping("/getList")
    public AjaxResult getList(DetectionTask task) {
        QueryWrapper<DetectionTask> queryWrapper = new QueryWrapper<>();
        if (task.getTaskId() != null) {
            queryWrapper.eq("task_id", task.getTaskId());
        }
        List<DetectionTask> taskList = detectionTaskMapper.selectList(queryWrapper);
        taskList.forEach(task1 -> {
            task1.setGtFile(hsiFileMapper.selectById(task1.getGtFileId()));
            task1.setMatFile(hsiFileMapper.selectById(task1.getMatFileId()));
            task1.setJpgFile(hsiFileMapper.selectById(task1.getJpgFileId()));
        });
        return AjaxResult.success("success", taskList);
    }

    @PostMapping("/evaluate")
    public AjaxResult evaluate(@RequestBody Map<String, Object> params) {
        Long taskID = ((Number) params.get("taskID")).longValue();
        Integer isRenew = (Integer) params.get("isRenew");
        String gtPath = (String) params.get("gtPath");

        DetectionTask task = detectionTaskMapper.selectById(taskID);
        task.setJpgFile(hsiFileMapper.selectOne(new LambdaQueryWrapper<HsiFile>().eq(HsiFile::getFileId, task.getJpgFileId())));
        task.setMatFile(hsiFileMapper.selectOne(new LambdaQueryWrapper<HsiFile>().eq(HsiFile::getFileId, task.getMatFileId())));
        task.setGtFile(hsiFileMapper.selectOne(new LambdaQueryWrapper<HsiFile>().eq(HsiFile::getStoragePath, gtPath)));
        if (task.getGtFileId() != null && isRenew == 0) {
            return AjaxResult.success("已存在数据", task);
        }
        task.setGtFileId(task.getGtFile().getFileId());
        detectionTaskMapper.updateById(task);
        task = predictService.executeEvaluate(task);
        return AjaxResult.success("评估成功", task);
    }


}