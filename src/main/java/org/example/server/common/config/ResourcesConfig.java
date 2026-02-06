package org.example.server.common.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.example.server.common.config.Config; // 假设你的配置类在这里

@Configuration
public class ResourcesConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 关键代码：建立 URL 到 本地磁盘 的映射
        // 意思是：访问 http://localhost:8089/profile/...
        // 实际上去读取 Config.getProfile() 配置的本地文件夹
        registry.addResourceHandler("/profile/**")
                .addResourceLocations("file:" + Config.getProfile() + "/");

        // 注意：addResourceLocations 必须以 "file:" 开头
        // 假设 Config.getProfile() 返回的是 "F:/Temp/uploadPath"
        // 最终效果是映射到 file:F:/Temp/uploadPath/
    }
}