package com.hezal.system.storage.domain;

/**
 * 已存储对象信息。
 *
 * @author trainmind
 */
public class StoredObject
{
    private String bucket;

    private String objectName;

    private String eTag;

    private long contentLength;

    public StoredObject()
    {
    }

    public StoredObject(String bucket, String objectName, String eTag, long contentLength)
    {
        this.bucket = bucket;
        this.objectName = objectName;
        this.eTag = eTag;
        this.contentLength = contentLength;
    }

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
}
