package com.hezal.system.storage.domain;

import java.time.Instant;
import java.util.Collections;
import java.util.Map;

/**
 * 对象元数据。
 *
 * @author trainmind
 */
public class ObjectMetadata
{
    private String bucket;

    private String objectName;

    private String eTag;

    private long contentLength;

    private String contentType;

    private Instant lastModified;

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

    public String geteTag()
    {
        return eTag;
    }

    public void seteTag(String eTag)
    {
        this.eTag = eTag;
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

    public Instant getLastModified()
    {
        return lastModified;
    }

    public void setLastModified(Instant lastModified)
    {
        this.lastModified = lastModified;
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
