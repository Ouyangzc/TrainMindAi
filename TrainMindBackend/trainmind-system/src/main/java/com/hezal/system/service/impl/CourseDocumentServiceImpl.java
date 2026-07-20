package com.hezal.system.service.impl;

import java.io.IOException;
import java.io.InputStream;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.CourseDocument;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.CourseModule;
import com.hezal.system.domain.DocumentParseTask;
import com.hezal.system.ai.AiDocumentParseClient;
import com.hezal.system.mapper.CourseDocumentMapper;
import com.hezal.system.mapper.CourseDocumentVersionMapper;
import com.hezal.system.mapper.KnowledgeBaseMapper;
import com.hezal.system.mapper.CourseModuleMapper;
import com.hezal.system.service.ICourseDocumentService;
import com.hezal.system.storage.CourseDocumentObjectNameGenerator;
import com.hezal.system.storage.ObjectStorageService;
import com.hezal.system.storage.domain.StoredObject;
import com.hezal.system.storage.domain.UploadObjectCommand;

/**
 * 课程资料业务实现。
 *
 * @author trainmind
 */
@Service
public class CourseDocumentServiceImpl implements ICourseDocumentService
{
    private static final long MAX_FILE_SIZE = 200L * 1024 * 1024;

    private static final Set<String> ALLOWED_EXTENSIONS = Set.of("pdf", "docx", "pptx", "xlsx");

    private final CourseDocumentMapper documentMapper;

    private final CourseDocumentVersionMapper versionMapper;
    private final KnowledgeBaseMapper knowledgeBaseMapper;

    private final CourseModuleMapper moduleMapper;

    private final ObjectStorageService objectStorageService;

    private final CourseDocumentObjectNameGenerator objectNameGenerator;

    private final AiDocumentParseClient aiDocumentParseClient;

    public CourseDocumentServiceImpl(CourseDocumentMapper documentMapper,
            CourseDocumentVersionMapper versionMapper, KnowledgeBaseMapper knowledgeBaseMapper,
            CourseModuleMapper moduleMapper,
            ObjectStorageService objectStorageService,
            CourseDocumentObjectNameGenerator objectNameGenerator,
            AiDocumentParseClient aiDocumentParseClient)
    {
        this.documentMapper = documentMapper;
        this.versionMapper = versionMapper;
        this.knowledgeBaseMapper = knowledgeBaseMapper;
        this.moduleMapper = moduleMapper;
        this.objectStorageService = objectStorageService;
        this.objectNameGenerator = objectNameGenerator;
        this.aiDocumentParseClient = aiDocumentParseClient;
    }

    @Override
    public List<CourseDocument> selectCourseDocumentList(CourseDocument document)
    {
        document.setTenantId(TrainMindConstants.DEFAULT_TENANT_ID);
        return documentMapper.selectCourseDocumentList(document);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CourseDocumentVersion uploadDocument(Long courseId, Long moduleId, String title,
            String remark, MultipartFile file, String username)
    {
        validateTitle(title);
        validateCourseAndModule(courseId, moduleId);
        String extension = validateFile(file);

        CourseDocument document = new CourseDocument();
        document.setTenantId(TrainMindConstants.DEFAULT_TENANT_ID);
        document.setCourseId(courseId);
        document.setModuleId(moduleId);
        document.setTitle(title.trim());
        document.setDocumentType(extension);
        document.setStatus(TrainMindConstants.COURSE_DOCUMENT_STATUS_ACTIVE);
        document.setCreateBy(username);
        document.setRemark(remark);
        documentMapper.insertCourseDocument(document);

        CourseDocumentVersion version = createVersion(document, 1, remark, file, extension, username);
        document.setLatestVersionId(version.getId());
        document.setUpdateBy(username);
        documentMapper.updateCourseDocument(document);
        return version;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CourseDocumentVersion uploadVersion(Long courseId, Long documentId,
            String remark, MultipartFile file, String username)
    {
        String extension = validateFile(file);
        CourseDocument document = documentMapper.lockCourseDocumentById(documentId);
        validateDocumentCourse(document, courseId);

        Integer maxVersionNo = versionMapper.selectMaxVersionNo(documentId);
        CourseDocumentVersion version = createVersion(document, maxVersionNo + 1,
                remark, file, extension, username);
        document.setLatestVersionId(version.getId());
        document.setDocumentType(extension);
        document.setUpdateBy(username);
        documentMapper.updateCourseDocument(document);
        return version;
    }

    @Override
    public List<CourseDocumentVersion> selectVersions(Long courseId, Long documentId)
    {
        validateDocumentCourse(documentMapper.selectCourseDocumentById(documentId), courseId);
        return versionMapper.selectVersionsByDocumentId(documentId);
    }

    @Override
    public CourseDocumentVersion selectVersion(Long courseId, Long documentId, Long versionId)
    {
        CourseDocumentVersion version = versionMapper.selectVersion(courseId, documentId, versionId);
        if (version == null)
        {
            throw new ServiceException("资料版本不存在");
        }
        return version;
    }

    @Override
    public InputStream openVersionStream(CourseDocumentVersion version)
    {
        return objectStorageService.getObject(version.getBucket(), version.getObjectName());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DocumentParseTask triggerParse(Long courseId, Long documentId, Long versionId, String username)
    {
        CourseDocumentVersion version = versionMapper.lockVersion(courseId, documentId, versionId);
        if (version == null)
        {
            throw new ServiceException("资料版本不存在");
        }
        if (TrainMindConstants.DOCUMENT_VERSION_STATUS_ARCHIVED.equals(version.getStatus()))
        {
            throw new ServiceException("已归档资料版本不能解析");
        }
        if (TrainMindConstants.DOCUMENT_VERSION_STATUS_PARSING.equals(version.getStatus()))
        {
            throw new ServiceException("资料版本正在解析中");
        }
        if (!StringUtils.hasText(version.getObjectName()))
        {
            throw new ServiceException("资料版本缺少对象存储信息");
        }

        DocumentParseTask task = aiDocumentParseClient.createTask(version);
        version.setStatus(TrainMindConstants.DOCUMENT_VERSION_STATUS_PARSING);
        version.setParseTaskId(task.getId());
        version.setParseErrorMessage("");
        version.setUpdateBy(username);
        versionMapper.updateCourseDocumentVersion(version);
        return task;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DocumentParseTask selectParseTask(Long courseId, Long documentId, Long versionId, String username)
    {
        CourseDocumentVersion version = selectVersion(courseId, documentId, versionId);
        if (version.getParseTaskId() == null)
        {
            throw new ServiceException("资料版本尚未创建解析任务");
        }

        DocumentParseTask task = aiDocumentParseClient.getTask(version.getParseTaskId());
        if (!documentId.equals(task.getDocumentId()) || !versionId.equals(task.getDocumentVersionId()))
        {
            throw new ServiceException("解析任务与资料版本不匹配");
        }

        String versionStatus = resolveVersionStatus(task.getStatus());
        String errorMessage = TrainMindConstants.DOCUMENT_VERSION_STATUS_FAILED.equals(versionStatus)
                ? task.getErrorMessage() : "";
        if (!versionStatus.equals(version.getStatus())
                || !org.apache.commons.lang3.StringUtils.equals(errorMessage, version.getParseErrorMessage()))
        {
            version.setStatus(versionStatus);
            version.setParseErrorMessage(errorMessage);
            version.setUpdateBy(username);
            versionMapper.updateCourseDocumentVersion(version);
        }
        return task;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int deleteCourseDocument(Long courseId, Long documentId)
    {
        validateDocumentCourse(documentMapper.lockCourseDocumentById(documentId), courseId);
        if (knowledgeBaseMapper.countDocumentReferences(documentId) > 0)
        {
            throw new ServiceException("资料已被知识库版本引用，不能删除");
        }
        versionMapper.deleteVersionsByDocumentId(documentId);
        return documentMapper.deleteCourseDocumentById(documentId);
    }

    private CourseDocumentVersion createVersion(CourseDocument document, Integer versionNo,
            String remark, MultipartFile file, String extension, String username)
    {
        CourseDocumentVersion version = new CourseDocumentVersion();
        version.setTenantId(document.getTenantId());
        version.setCourseId(document.getCourseId());
        version.setModuleId(document.getModuleId());
        version.setDocumentId(document.getId());
        version.setVersionNo(versionNo);
        version.setOriginalFilename(normalizeFilename(file.getOriginalFilename()));
        version.setFileExt(extension);
        version.setContentType(file.getContentType());
        version.setFileSize(file.getSize());
        version.setStatus(TrainMindConstants.DOCUMENT_VERSION_STATUS_UPLOADED);
        version.setCreateBy(username);
        version.setRemark(remark);
        versionMapper.insertCourseDocumentVersion(version);

        String objectName = objectNameGenerator.generate(version.getTenantId(), version.getCourseId(),
                version.getModuleId(), version.getDocumentId(), version.getId(), extension);
        MessageDigest digest = createMd5Digest();
        StoredObject storedObject;
        try (InputStream input = file.getInputStream();
                DigestInputStream digestInput = new DigestInputStream(input, digest))
        {
            UploadObjectCommand command = new UploadObjectCommand();
            command.setObjectName(objectName);
            command.setInputStream(digestInput);
            command.setContentLength(file.getSize());
            command.setContentType(file.getContentType());
            storedObject = objectStorageService.putObject(command);
        }
        catch (IOException e)
        {
            throw new ServiceException("读取上传文件失败").setDetailMessage(e.getMessage());
        }

        registerObjectRollback(storedObject.getBucket(), storedObject.getObjectName());
        version.setBucket(storedObject.getBucket());
        version.setObjectName(storedObject.getObjectName());
        version.setChecksumMd5(HexFormat.of().formatHex(digest.digest()));
        version.setUpdateBy(username);
        versionMapper.updateCourseDocumentVersion(version);
        return version;
    }

    private void registerObjectRollback(String bucket, String objectName)
    {
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization()
        {
            @Override
            public void afterCompletion(int status)
            {
                if (status == STATUS_ROLLED_BACK)
                {
                    objectStorageService.deleteObject(bucket, objectName);
                }
            }
        });
    }

    private String validateFile(MultipartFile file)
    {
        if (file == null || file.isEmpty())
        {
            throw new ServiceException("上传文件不能为空");
        }
        if (file.getSize() > MAX_FILE_SIZE)
        {
            throw new ServiceException("单个文件不能超过200MB");
        }
        String extension = StringUtils.getFilenameExtension(file.getOriginalFilename());
        extension = extension == null ? "" : extension.toLowerCase(Locale.ROOT);
        if (!ALLOWED_EXTENSIONS.contains(extension))
        {
            throw new ServiceException("仅支持pdf、docx、pptx、xlsx文件");
        }
        return extension;
    }

    private void validateTitle(String title)
    {
        if (!StringUtils.hasText(title))
        {
            throw new ServiceException("资料标题不能为空");
        }
        if (title.trim().length() > 255)
        {
            throw new ServiceException("资料标题长度不能超过255个字符");
        }
    }

    private void validateDocumentCourse(CourseDocument document, Long courseId)
    {
        if (document == null || !courseId.equals(document.getCourseId()))
        {
            throw new ServiceException("课程资料不存在");
        }
    }

    private void validateCourseAndModule(Long courseId, Long moduleId)
    {
        if (courseId == null || documentMapper.countCourseById(courseId) == 0)
        {
            throw new ServiceException("课程不存在");
        }
        if (moduleId == null)
        {
            return;
        }
        CourseModule module = moduleMapper.selectCourseModuleById(moduleId);
        if (module == null || !courseId.equals(module.getCourseId()))
        {
            throw new ServiceException("课程模块不存在");
        }
    }

    private String normalizeFilename(String filename)
    {
        String normalized = StringUtils.getFilename(filename);
        if (!StringUtils.hasText(normalized))
        {
            throw new ServiceException("原始文件名不能为空");
        }
        if (normalized.length() > 255)
        {
            throw new ServiceException("原始文件名长度不能超过255个字符");
        }
        return normalized;
    }

    private MessageDigest createMd5Digest()
    {
        try
        {
            return MessageDigest.getInstance("MD5");
        }
        catch (NoSuchAlgorithmException e)
        {
            throw new IllegalStateException("当前JDK不支持MD5", e);
        }
    }

    private String resolveVersionStatus(String taskStatus)
    {
        if (TrainMindConstants.PARSE_TASK_STATUS_SUCCESS.equals(taskStatus))
        {
            return TrainMindConstants.DOCUMENT_VERSION_STATUS_PARSED;
        }
        if (TrainMindConstants.PARSE_TASK_STATUS_FAILED.equals(taskStatus)
                || TrainMindConstants.PARSE_TASK_STATUS_CANCELLED.equals(taskStatus))
        {
            return TrainMindConstants.DOCUMENT_VERSION_STATUS_FAILED;
        }
        if (TrainMindConstants.PARSE_TASK_STATUS_PENDING.equals(taskStatus)
                || TrainMindConstants.PARSE_TASK_STATUS_RUNNING.equals(taskStatus))
        {
            return TrainMindConstants.DOCUMENT_VERSION_STATUS_PARSING;
        }
        throw new ServiceException("未知解析任务状态：" + taskStatus);
    }
}
