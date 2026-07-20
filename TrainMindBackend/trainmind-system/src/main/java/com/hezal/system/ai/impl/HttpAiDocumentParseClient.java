package com.hezal.system.ai.impl;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.ai.AiDocumentParseClient;
import com.hezal.system.ai.AiKnowledgeBaseClient;
import com.hezal.system.ai.config.AiServiceProperties;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.DocumentParseTask;
import com.hezal.system.domain.KnowledgeBaseBuildTask;

/**
 * 基于HTTP的AI文档解析客户端。
 *
 * @author trainmind
 */
@Component
public class HttpAiDocumentParseClient implements AiDocumentParseClient, AiKnowledgeBaseClient
{
    private final AiServiceProperties properties;

    private final ObjectMapper objectMapper;

    private final HttpClient httpClient;

    public HttpAiDocumentParseClient(AiServiceProperties properties, ObjectMapper objectMapper)
    {
        this.properties = properties;
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                // Uvicorn 不支持明文 HTTP/2 升级，内部接口固定使用 HTTP/1.1。
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(properties.getConnectTimeoutSeconds()))
                .build();
    }

    @Override
    public DocumentParseTask createTask(CourseDocumentVersion version)
    {
        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("course_id", version.getCourseId());
        requestBody.put("document_id", version.getDocumentId());
        requestBody.put("object_name", version.getObjectName());
        requestBody.put("file_ext", version.getFileExt());
        requestBody.put("checksum_md5", version.getChecksumMd5());

        JsonNode body = send("POST",
                "/internal/v1/documents/" + version.getId() + "/parse", requestBody);
        DocumentParseTask task = new DocumentParseTask();
        task.setId(requiredLong(body, "task_id"));
        task.setDocumentId(version.getDocumentId());
        task.setDocumentVersionId(version.getId());
        task.setStatus(requiredText(body, "status"));
        return task;
    }

    @Override
    public DocumentParseTask getTask(Long taskId)
    {
        JsonNode body = send("GET", "/internal/v1/document-parse-tasks/" + taskId, null);
        DocumentParseTask task = new DocumentParseTask();
        task.setId(requiredLong(body, "task_id"));
        task.setDocumentId(requiredLong(body, "document_id"));
        task.setDocumentVersionId(requiredLong(body, "document_version_id"));
        task.setStatus(requiredText(body, "status"));
        task.setCurrentStep(text(body, "current_step"));
        task.setProgress(body.path("progress").isNumber() ? body.path("progress").asInt() : 0);
        task.setErrorCode(text(body, "error_code"));
        task.setErrorMessage(text(body, "error_message"));
        task.setRetryCount(body.path("retry_count").isNumber() ? body.path("retry_count").asInt() : 0);
        return task;
    }

    @Override
    public KnowledgeBaseBuildTask createBuildTask(Long knowledgeBaseVersionId)
    {
        JsonNode body = send("POST",
                "/internal/v1/kb-versions/" + knowledgeBaseVersionId + "/build", null);
        KnowledgeBaseBuildTask task = new KnowledgeBaseBuildTask();
        task.setId(requiredLong(body, "task_id"));
        task.setStatus(requiredText(body, "status"));
        task.setTaskType("build_knowledge_base_version");
        return task;
    }

    @Override
    public KnowledgeBaseBuildTask getBuildTask(Long taskId)
    {
        JsonNode body = send("GET", "/internal/v1/kb-tasks/" + taskId, null);
        KnowledgeBaseBuildTask task = new KnowledgeBaseBuildTask();
        task.setId(requiredLong(body, "task_id"));
        task.setTaskType(text(body, "task_type"));
        task.setStatus(requiredText(body, "status"));
        task.setCurrentStep(text(body, "current_step"));
        task.setProgress(body.path("progress").isNumber() ? body.path("progress").asInt() : 0);
        task.setErrorCode(text(body, "error_code"));
        task.setErrorMessage(text(body, "error_message"));
        task.setRetryCount(body.path("retry_count").isNumber() ? body.path("retry_count").asInt() : 0);
        return task;
    }

    private JsonNode send(String method, String path, Object requestBody)
    {
        try
        {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(normalizedBaseUrl() + path))
                    .timeout(Duration.ofSeconds(properties.getRequestTimeoutSeconds()))
                    .header("X-Internal-Token", properties.getInternalToken())
                    .header("Accept", "application/json");
            if ("POST".equals(method))
            {
                String json = objectMapper.writeValueAsString(
                        requestBody == null ? Map.of() : requestBody);
                builder.header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(json));
            }
            else
            {
                builder.GET();
            }

            HttpResponse<String> response = httpClient.send(builder.build(),
                    HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() < 200 || response.statusCode() >= 300)
            {
                throw new ServiceException("AI服务请求失败，HTTP状态码：" + response.statusCode())
                        .setDetailMessage(response.body());
            }
            return objectMapper.readTree(response.body());
        }
        catch (ServiceException e)
        {
            throw e;
        }
        catch (InterruptedException e)
        {
            Thread.currentThread().interrupt();
            throw new ServiceException("AI服务请求被中断").setDetailMessage(e.getMessage());
        }
        catch (Exception e)
        {
            throw new ServiceException("AI服务请求失败").setDetailMessage(e.getMessage());
        }
    }

    private String normalizedBaseUrl()
    {
        String baseUrl = properties.getBaseUrl();
        return baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
    }

    private Long requiredLong(JsonNode body, String field)
    {
        if (!body.path(field).isIntegralNumber())
        {
            throw new ServiceException("AI服务响应缺少字段：" + field);
        }
        return body.path(field).asLong();
    }

    private String requiredText(JsonNode body, String field)
    {
        String value = text(body, field);
        if (value == null || value.isBlank())
        {
            throw new ServiceException("AI服务响应缺少字段：" + field);
        }
        return value;
    }

    private String text(JsonNode body, String field)
    {
        JsonNode value = body.path(field);
        return value.isMissingNode() || value.isNull() ? null : value.asText();
    }
}
