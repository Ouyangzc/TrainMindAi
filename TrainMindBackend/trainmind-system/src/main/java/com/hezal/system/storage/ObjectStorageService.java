package com.hezal.system.storage;

import java.io.InputStream;

import com.hezal.system.storage.domain.ObjectMetadata;
import com.hezal.system.storage.domain.StoredObject;
import com.hezal.system.storage.domain.UploadObjectCommand;

/**
 * 对象存储服务。
 *
 * 业务层只依赖该接口，不感知 SeaweedFS、MinIO 或云厂商实现。
 *
 * @author trainmind
 */
public interface ObjectStorageService
{
    /**
     * 上传对象。
     *
     * @param command 上传命令
     * @return 已存储对象信息
     */
    StoredObject putObject(UploadObjectCommand command);

    /**
     * 获取对象流，调用方负责关闭返回的输入流。
     *
     * @param bucket 存储桶，为空时使用默认存储桶
     * @param objectName 对象Key
     * @return 对象输入流
     */
    InputStream getObject(String bucket, String objectName);

    /**
     * 查询对象元数据。
     *
     * @param bucket 存储桶，为空时使用默认存储桶
     * @param objectName 对象Key
     * @return 对象元数据
     */
    ObjectMetadata headObject(String bucket, String objectName);

    /**
     * 删除对象。
     *
     * @param bucket 存储桶，为空时使用默认存储桶
     * @param objectName 对象Key
     */
    void deleteObject(String bucket, String objectName);
}
