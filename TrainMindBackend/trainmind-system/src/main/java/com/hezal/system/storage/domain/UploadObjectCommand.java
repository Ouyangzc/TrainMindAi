package com.hezal.system.storage.domain;

import java.io.InputStream;
import java.util.Collections;
import java.util.Map;

/**
 * 上传对象命令。
 *
 * @author trainmind
 */
public class UploadObjectCommand
{
    private String bucket;

    private String objectName;

    private InputStream inputStream;

    private long contentLength;

    private String contentType;

    private Map<String, String> metadata = Collections.emptyMap();

    public String getBucket()
    {
        return bucket;
    }

    public void setBucket(String bucket)
    {
        this.bucket = bucket;
    }

    public String getObjectName()
    {
        return objectName;
    }

    public void setObjectName(String objectName)
    {
        this.objectName = objectName;
    }

    public InputStream getInputStream()
    {
        return inputStream;
    }

    public void setInputStream(InputStream inputStream)
    {
        this.inputStream = inputStream;
    }

    public long getContentLength()
    {
        return contentLength;
    }

    public void setContentLength(long contentLength)
    {
        this.contentLength = contentLength;
    }

    public String getContentType()
    {
        return contentType;
    }

    public void setContentType(String contentType)
    {
        this.contentType = contentType;
    }

    public Map<String, String> getMetadata()
    {
        return metadata;
    }

    public void setMetadata(Map<String, String> metadata)
    {
        this.metadata = metadata == null ? Collections.emptyMap() : metadata;
    }
}
