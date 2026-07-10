package com.hezal.system.storage;

import java.util.Locale;

import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.hezal.common.exception.ServiceException;
import com.hezal.common.utils.uuid.IdUtils;

/**
 * 课程资料对象Key生成器。
 *
 * @author trainmind
 */
@Component
public class CourseDocumentObjectNameGenerator
{
    private static final String PUBLIC_MODULE = "public";

    /**
     * 生成课程资料版本对象Key。
     *
     * @param tenantId 租户ID
     * @param courseId 课程ID
     * @param moduleId 模块ID，空表示课程公共资料
     * @param documentId 资料ID
     * @param versionId 资料版本ID
     * @param fileExt 文件扩展名
     * @return 对象Key
     */
    public String generate(Long tenantId, Long courseId, Long moduleId, Long documentId, Long versionId, String fileExt)
    {
        validateRequired("租户ID", tenantId);
        validateRequired("课程ID", courseId);
        validateRequired("资料ID", documentId);
        validateRequired("资料版本ID", versionId);
        if (!StringUtils.hasText(fileExt))
        {
            throw new ServiceException("文件扩展名不能为空");
        }

        String moduleSegment = moduleId == null ? PUBLIC_MODULE : String.valueOf(moduleId);
        String normalizedExt = normalizeExtension(fileExt);
        return "tenants/" + tenantId
                + "/courses/" + courseId
                + "/modules/" + moduleSegment
                + "/documents/" + documentId
                + "/versions/" + versionId
                + "/" + IdUtils.fastSimpleUUID() + "." + normalizedExt;
    }

    private void validateRequired(String fieldName, Long value)
    {
        if (value == null)
        {
            throw new ServiceException(fieldName + "不能为空");
        }
    }

    private String normalizeExtension(String fileExt)
    {
        String ext = fileExt.trim().toLowerCase(Locale.ROOT);
        if (ext.startsWith("."))
        {
            ext = ext.substring(1);
        }
        if (!StringUtils.hasText(ext) || ext.contains("/") || ext.contains("\\"))
        {
            throw new ServiceException("文件扩展名不合法");
        }
        return ext;
    }
}
