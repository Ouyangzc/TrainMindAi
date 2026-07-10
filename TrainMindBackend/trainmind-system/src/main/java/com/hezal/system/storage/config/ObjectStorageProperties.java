package com.hezal.system.storage.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 对象存储配置。
 *
 * @author trainmind
 */
@ConfigurationProperties(prefix = "trainmind.storage")
public class ObjectStorageProperties
{
    /** 是否启用对象存储 */
    private boolean enabled = true;

    /** 存储类型，第一阶段固定使用 s3 */
    private String type = "s3";

    /** S3兼容端点 */
    private String endpoint = "http://127.0.0.1:8333";

    /** 区域，SeaweedFS本地开发可使用默认值 */
    private String region = "us-east-1";

    /** 默认存储桶 */
    private String bucket = "trainmind-docs";

    /** 访问密钥 */
    private String accessKey = "trainmind";

    /** 访问密钥Secret */
    private String secretKey = "trainmind-secret";

    /** 是否使用Path Style访问，SeaweedFS本地部署需要开启 */
    private boolean pathStyleAccess = true;

    public boolean isEnabled()
    {
        return enabled;
    }

    public void setEnabled(boolean enabled)
    {
        this.enabled = enabled;
    }

    public String getType()
    {
        return type;
    }

    public void setType(String type)
    {
        this.type = type;
    }

    public String getEndpoint()
    {
        return endpoint;
    }

    public void setEndpoint(String endpoint)
    {
        this.endpoint = endpoint;
    }

    public String getRegion()
    {
        return region;
    }

    public void setRegion(String region)
    {
        this.region = region;
    }

    public String getBucket()
    {
        return bucket;
    }

    public void setBucket(String bucket)
    {
        this.bucket = bucket;
    }

    public String getAccessKey()
    {
        return accessKey;
    }

    public void setAccessKey(String accessKey)
    {
        this.accessKey = accessKey;
    }

    public String getSecretKey()
    {
        return secretKey;
    }

    public void setSecretKey(String secretKey)
    {
        this.secretKey = secretKey;
    }

    public boolean isPathStyleAccess()
    {
        return pathStyleAccess;
    }

    public void setPathStyleAccess(boolean pathStyleAccess)
    {
        this.pathStyleAccess = pathStyleAccess;
    }
}
