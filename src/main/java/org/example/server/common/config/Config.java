package org.example.server.common.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 读取项目相关配置
 *
 */
@Data
@Component
@ConfigurationProperties(prefix = "file")
public class Config {

    /**
     * 上传路径
     */
    private static String profile;

    /*
     * 输出路径
     * */
    private static String outputPath;

    /**
     * 获取地址开关
     */
    private static boolean addressEnabled;

    /**
     * 验证码类型
     */
    private static String captchaType;


    public static String getProfile() {
        return profile;
    }

    public void setProfile(String profile) {
        Config.profile = profile;
    }

    public static String getOutputPath() {
        return outputPath;
    }

    public void setOutputPath(String outputPath) {
        Config.outputPath = outputPath;
    }

    public static boolean isAddressEnabled() {
        return addressEnabled;
    }

    public void setAddressEnabled(boolean addressEnabled) {
        Config.addressEnabled = addressEnabled;
    }

    public static String getCaptchaType() {
        return captchaType;
    }

    public void setCaptchaType(String captchaType) {
        Config.captchaType = captchaType;
    }

    /**
     * 获取导入上传路径
     */
    public static String getImportPath() {
        return getProfile() + "/import";
    }

    /**
     * 获取头像上传路径
     */
    public static String getAvatarPath() {
        return getProfile() + "/avatar";
    }

    /**
     * 获取下载路径
     */
    public static String getDownloadPath() {
        return getProfile() + "/download/";
    }

    /**
     * 获取上传路径
     */
    public static String getUploadPath() {
        return getProfile() + "/upload";
    }

    /*
     * 获取绝对路径*/
    public static String getabsolutePath(String rawPath) {
        String dbPath = rawPath.replace("\\", "/");
        // 转换为绝对路径传给 Flask
        String profilePath = getProfile().replace("\\", "/");
        return profilePath + dbPath.substring("/profile".length());
    }

    /**
     * 统一路径处理逻辑：绝对路径 -> /profile 相对路径，并统一斜杠
     */
    public static String formatPath(String rawAbsolutePath) {
        if (rawAbsolutePath == null) return null;

        // 统一为正斜杠
        String absolutePath = rawAbsolutePath.replace("\\", "/");
        String profileRoot = Config.getProfile().replace("\\", "/");

        String relativePath = "";
        if (absolutePath.contains(profileRoot)) {
            relativePath = absolutePath.substring(profileRoot.length());
        } else {
            relativePath = absolutePath;
        }

        // 确保以 / 开头并拼接前缀
        if (!relativePath.startsWith("/")) {
            relativePath = "/" + relativePath;
        }
        return "/profile" + relativePath;
    }
}
