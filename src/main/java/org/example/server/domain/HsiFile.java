package org.example.server.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("hsi_file")
public class HsiFile {
    @TableId(type = IdType.AUTO)
    private Long fileId;
    private String fileName;
    private String newName;
    private String fileMd5;
    private String storagePath;
    private String fileType; // mat 或 jpg
    private LocalDateTime uploadTime;
}