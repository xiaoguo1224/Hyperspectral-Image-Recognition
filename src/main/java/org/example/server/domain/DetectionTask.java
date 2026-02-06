package org.example.server.domain;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("detection_task")
public class DetectionTask {
    @TableId(type = IdType.AUTO)
    private Long taskId;
    private String taskName;
    private Long matFileId;
    private Long jpgFileId;
    private String modelName;
    private String maskPath;
    private String spectralData; // 存储JSON格式反射率
    private Double mapValue;
    private Double f1Score;
    private Double latency;
    private Integer status; // 0-待机, 1-识别中, 2-已完成
    private LocalDateTime createTime;
    private LocalDateTime finishTime;
}