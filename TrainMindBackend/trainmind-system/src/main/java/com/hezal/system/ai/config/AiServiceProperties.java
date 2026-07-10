package com.hezal.system.ai.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * AI内部服务配置。
 *
 * @author trainmind
 */
@Component
@ConfigurationProperties(prefix = "trainmind.ai-service")
public class AiServiceProperties
{
    private String baseUrl = "http://127.0.0.1:8000";

    private String internalToken = "change-me";

    private int connectTimeoutSeconds = 5;

    private int requestTimeoutSeconds = 30;

    public String getBaseUrl() { return baseUrl; }
    public void setBaseUrl(String baseUrl) { this.baseUrl = baseUrl; }
    public String getInternalToken() { return internalToken; }
    public void setInternalToken(String internalToken) { this.internalToken = internalToken; }
    public int getConnectTimeoutSeconds() { return connectTimeoutSeconds; }
    public void setConnectTimeoutSeconds(int connectTimeoutSeconds) { this.connectTimeoutSeconds = connectTimeoutSeconds; }
    public int getRequestTimeoutSeconds() { return requestTimeoutSeconds; }
    public void setRequestTimeoutSeconds(int requestTimeoutSeconds) { this.requestTimeoutSeconds = requestTimeoutSeconds; }
}
