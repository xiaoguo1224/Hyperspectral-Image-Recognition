package org.example.server.common.config;

import jakarta.servlet.http.HttpServletRequest;
import org.example.server.common.exception.base.BaseException;
import org.example.server.common.utils.ServletUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

/**
 * 服务相关配置
 *
 */
@Component
public class ServerConfig {


    private static String pythonUrl;

    @Value("${predict.url}")
    public void setPythonUrl(String url) {
        ServerConfig.pythonUrl = url;
    }

    private static final RestTemplate restTemplate = new RestTemplate();

    /**
     * 获取完整的请求路径，包括：域名，端口，上下文访问路径
     *
     * @return 服务地址
     */
    public String getUrl() {
        HttpServletRequest request = ServletUtils.getRequest();
        return getDomain(request);
    }

    public static String getDomain(HttpServletRequest request) {
        StringBuffer url = request.getRequestURL();
        String contextPath = request.getServletContext().getContextPath();
        return url.delete(url.length() - request.getRequestURI().length(), url.length()).append(contextPath).toString();
    }

    public static Map<String, Object> getResponse(String pythonApi, Map<String, Object> request) {

        String fullUrl = pythonUrl + pythonApi;
        try {
            Map response = restTemplate.postForObject(fullUrl, request, Map.class);
            if (response != null && (Integer) response.get("code") == 200) {
                return response;
            } else {
                throw new BaseException("请求服务器错误");
            }
        } catch (Exception e) {
            throw new RuntimeException();
        }

    }
}
