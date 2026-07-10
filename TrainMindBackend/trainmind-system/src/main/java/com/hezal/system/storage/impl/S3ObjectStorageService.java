package com.hezal.system.storage.impl;

import java.io.InputStream;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.hezal.common.exception.ServiceException;
import com.hezal.system.storage.ObjectStorageService;
import com.hezal.system.storage.config.ObjectStorageProperties;
import com.hezal.system.storage.domain.ObjectMetadata;
import com.hezal.system.storage.domain.StoredObject;
import com.hezal.system.storage.domain.UploadObjectCommand;

import software.amazon.awssdk.core.ResponseInputStream;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.HeadObjectRequest;
import software.amazon.awssdk.services.s3.model.HeadObjectResponse;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectResponse;

/**
 * S3兼容对象存储实现。
 *
 * @author trainmind
 */
@Service
@ConditionalOnProperty(prefix = "trainmind.storage", name = "enabled", havingValue = "true", matchIfMissing = true)
public class S3ObjectStorageService implements ObjectStorageService
{
    private final S3Client s3Client;

    private final ObjectStorageProperties properties;

    public S3ObjectStorageService(S3Client s3Client, ObjectStorageProperties properties)
    {
        this.s3Client = s3Client;
        this.properties = properties;
    }

    @Override
    public StoredObject putObject(UploadObjectCommand command)
    {
        validateUploadCommand(command);
        String bucket = resolveBucket(command.getBucket());

        PutObjectRequest.Builder requestBuilder = PutObjectRequest.builder()
                .bucket(bucket)
                .key(command.getObjectName())
                .metadata(command.getMetadata());

        if (StringUtils.hasText(command.getContentType()))
        {
            requestBuilder.contentType(command.getContentType());
        }

        PutObjectResponse response = s3Client.putObject(requestBuilder.build(),
                RequestBody.fromInputStream(command.getInputStream(), command.getContentLength()));
        return new StoredObject(bucket, command.getObjectName(), response.eTag(), command.getContentLength());
    }

    @Override
    public InputStream getObject(String bucket, String objectName)
    {
        validateObjectName(objectName);
        GetObjectRequest request = GetObjectRequest.builder()
                .bucket(resolveBucket(bucket))
                .key(objectName)
                .build();
        ResponseInputStream<GetObjectResponse> response = s3Client.getObject(request);
        return response;
    }

    @Override
    public ObjectMetadata headObject(String bucket, String objectName)
    {
        validateObjectName(objectName);
        String resolvedBucket = resolveBucket(bucket);
        HeadObjectResponse response = s3Client.headObject(HeadObjectRequest.builder()
                .bucket(resolvedBucket)
                .key(objectName)
                .build());

        ObjectMetadata metadata = new ObjectMetadata();
        metadata.setBucket(resolvedBucket);
        metadata.setObjectName(objectName);
        metadata.seteTag(response.eTag());
        metadata.setContentLength(response.contentLength());
        metadata.setContentType(response.contentType());
        metadata.setLastModified(response.lastModified());
        metadata.setMetadata(response.metadata());
        return metadata;
    }

    @Override
    public void deleteObject(String bucket, String objectName)
    {
        validateObjectName(objectName);
        s3Client.deleteObject(DeleteObjectRequest.builder()
                .bucket(resolveBucket(bucket))
                .key(objectName)
                .build());
    }

    private void validateUploadCommand(UploadObjectCommand command)
    {
        if (command == null)
        {
            throw new ServiceException("上传对象不能为空");
        }
        validateObjectName(command.getObjectName());
        if (command.getInputStream() == null)
        {
            throw new ServiceException("上传对象输入流不能为空");
        }
        if (command.getContentLength() < 0)
        {
            throw new ServiceException("上传对象大小不能小于0");
        }
    }

    private void validateObjectName(String objectName)
    {
        if (!StringUtils.hasText(objectName))
        {
            throw new ServiceException("对象Key不能为空");
        }
    }

    private String resolveBucket(String bucket)
    {
        String resolvedBucket = StringUtils.hasText(bucket) ? bucket : properties.getBucket();
        if (!StringUtils.hasText(resolvedBucket))
        {
            throw new ServiceException("对象存储Bucket不能为空");
        }
        return resolvedBucket;
    }
}
