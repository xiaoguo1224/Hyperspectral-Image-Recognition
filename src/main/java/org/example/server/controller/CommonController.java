package org.example.server.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.example.server.common.config.Config;
import org.example.server.common.config.ServerConfig;
import org.example.server.common.core.domain.AjaxResult;
import org.example.server.common.utils.StringUtils;
import org.example.server.common.utils.file.FileTypeUtils;
import org.example.server.common.utils.file.FileUploadUtils;
import org.example.server.common.utils.file.FileUtils;
import org.example.server.domain.HsiFile;
import org.example.server.mapper.HsiFileMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/common")
public class CommonController {

    @Autowired
    private ServerConfig serverConfig;
    @Autowired
    private HsiFileMapper hsiFileMapper;
    private static final String FILE_DELIMETER = ",";

    /**
     * 通用上传请求（多个）
     */
    @PostMapping("/uploads")
    public AjaxResult uploadFiles(List<MultipartFile> files) throws Exception {
        try {
            // 上传文件路径
            String filePath = Config.getUploadPath();
            List<Integer> ids = new ArrayList<>();
            List<String> urls = new ArrayList<String>();
            List<String> fileNames = new ArrayList<String>();
            List<String> newFileNames = new ArrayList<String>();
            List<String> originalFilenames = new ArrayList<String>();
            for (MultipartFile file : files) {
                // 上传并返回新文件名称

                String md5 = FileUtils.getFileMd5(file);

                HsiFile existingFile = hsiFileMapper.selectOne(
                        new LambdaQueryWrapper<HsiFile>().eq(HsiFile::getFileMd5, md5)
                );
                String fileName;
                String originalFilename = file.getOriginalFilename();

                if (existingFile != null) {
                    // 命中缓存：直接使用已存在的路径（实现秒传）
                    fileName = existingFile.getStoragePath();
                    System.out.println("文件已存在，触发秒传逻辑：" + originalFilename);
                } else {
                    // 未命中：执行物理上传
                    fileName = FileUploadUtils.upload(filePath, file);

                    // 保存新文件记录到数据库
                    HsiFile hsiFile = new HsiFile();
                    hsiFile.setFileName(originalFilename);
                    hsiFile.setFileMd5(md5);
                    hsiFile.setStoragePath(fileName);
                    // 根据你提供的 FileTypeUtils 获取类型
                    hsiFile.setFileType(FileTypeUtils.getFileType(originalFilename));
                    hsiFile.setUploadTime(LocalDateTime.now());
                    hsiFile.setNewName(FileUtils.getName(fileName));
                    hsiFileMapper.insert(hsiFile);
                }

                String url = serverConfig.getUrl() + fileName;
                urls.add(url);
                fileNames.add(fileName);
                newFileNames.add(FileUtils.getName(fileName));
                originalFilenames.add(originalFilename);
            }
            AjaxResult ajax = AjaxResult.success();
            ajax.put("urls", StringUtils.join(urls, FILE_DELIMETER));
            ajax.put("fileNames", StringUtils.join(fileNames, FILE_DELIMETER));
            ajax.put("newFileNames", StringUtils.join(newFileNames, FILE_DELIMETER));
            ajax.put("originalFilenames", StringUtils.join(originalFilenames, FILE_DELIMETER));
            return ajax;
        } catch (Exception e) {
            return AjaxResult.error(e.getMessage());
        }
    }
}
