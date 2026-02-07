package org.example.server.domain;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@TableName("detection_task")
@NoArgsConstructor
@AllArgsConstructor
public class DetectionTask {
    @TableId(type = IdType.AUTO)
    private Long taskId;
    private String taskName;
    private Long matFileId;
    private Long jpgFileId;
    private Long gtFileId;
    private String modelName;
    private String maskPath;
    private String spectralData; // 存储JSON格式反射率
    private Double mae;
    private Double f1;
    private Double pred;
    private Double rec;
    private Double auc;
    private Double cc;
    private Double nss;
    private Integer status; // 0-待机, 1-识别中, 2-已完成
    private LocalDateTime createTime;
    private LocalDateTime finishTime;

    @TableField(exist = false)
    private HsiFile matFile;
    @TableField(exist = false)
    private HsiFile jpgFile;
    @TableField(exist = false)
    private HsiFile gtFile;
}