package com.hezal.system.ai.impl;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Component;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.ai.AiQaClient;
import com.hezal.system.ai.config.AiServiceProperties;
import com.hezal.system.domain.dto.AiQaAnswer;
import com.hezal.system.domain.dto.AiQaRequest;

/** 基于 HTTP 的 AI 课程问答客户端。 */
@Component
public class HttpAiQaClient implements AiQaClient
{
    private final AiServiceProperties properties;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;

    public HttpAiQaClient(AiServiceProperties properties, ObjectMapper objectMapper)
    {
        this.properties = properties;
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(properties.getConnectTimeoutSeconds()))
                .build();
    }

    @Override
    public AiQaAnswer answer(AiQaRequest request)
    {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("user_id", request.getUserId());
        body.put("course_id", request.getCourseId());
        body.put("kb_version_id", request.getKnowledgeBaseVersionId());
        body.put("session_id", request.getSessionId());
        body.put("message_id", request.getMessageId());
        body.put("question", request.getQuestion());
        try
        {
            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl() + "/internal/v1/qa/answer"))
                    .timeout(Duration.ofSeconds(properties.getRequestTimeoutSeconds()))
                    .header("X-Internal-Token", properties.getInternalToken())
                    .header("Accept", "application/json")
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                    .build();
            HttpResponse<String> response = httpClient.send(httpRequest,
                    HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() < 200 || response.statusCode() >= 300)
            {
                throw new ServiceException("AI问答服务请求失败，HTTP状态码：" + response.statusCode())
                        .setDetailMessage(response.body());
            }
            return objectMapper.readValue(response.body(), AiQaAnswer.class);
        }
        catch (ServiceException e)
        {
            throw e;
        }
        catch (InterruptedException e)
        {
            Thread.currentThread().interrupt();
            throw new ServiceException("AI问答请求被中断").setDetailMessage(e.getMessage());
        }
        catch (Exception e)
        {
            throw new ServiceException("AI问答服务请求失败").setDetailMessage(e.getMessage());
        }
    }

    private String baseUrl()
    {
        String value = properties.getBaseUrl();
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }
}
