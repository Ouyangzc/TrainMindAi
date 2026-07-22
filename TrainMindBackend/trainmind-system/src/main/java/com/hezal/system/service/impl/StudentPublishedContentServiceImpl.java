package com.hezal.system.service.impl;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import com.github.pagehelper.PageHelper;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.dto.StudentDocumentQuery;
import com.hezal.system.domain.Course;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.vo.student.StudentCourseContext;
import com.hezal.system.domain.vo.student.StudentCourseModuleVO;
import com.hezal.system.domain.vo.student.StudentCourseOutlineVO;
import com.hezal.system.domain.vo.student.StudentPublishedDocumentVO;
import com.hezal.system.mapper.StudentPublishedContentMapper;
import com.hezal.system.mapper.CourseMapper;
import com.hezal.system.service.CourseAccessService;
import com.hezal.system.service.ICourseDocumentService;
import com.hezal.system.service.IStudentPublishedContentService;

/** 学员端当前发布内容只读服务实现。 */
@Service
public class StudentPublishedContentServiceImpl implements IStudentPublishedContentService
{
    private static final String PUBLIC_MODULE_KEY = "public";
    private final CourseAccessService courseAccessService;
    private final StudentPublishedContentMapper contentMapper;
    private final CourseMapper courseMapper;
    private final ICourseDocumentService documentService;

    public StudentPublishedContentServiceImpl(CourseAccessService courseAccessService,
            StudentPublishedContentMapper contentMapper, CourseMapper courseMapper,
            ICourseDocumentService documentService)
    {
        this.courseAccessService = courseAccessService;
        this.contentMapper = contentMapper;
        this.courseMapper = courseMapper;
        this.documentService = documentService;
    }

    @Override
    public StudentCourseOutlineVO selectOutline(Long courseId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        List<StudentPublishedDocumentVO> documents = contentMapper.selectPublishedDocuments(
                context.getTenantId(), courseId, context.getPublishedVersionId(), null);
        Map<String, StudentCourseModuleVO> grouped = new LinkedHashMap<>();
        for (StudentPublishedDocumentVO document : documents)
        {
            String key = document.getModuleId() == null
                    ? PUBLIC_MODULE_KEY : document.getModuleId().toString();
            StudentCourseModuleVO module = grouped.computeIfAbsent(key, ignored -> createModule(document));
            module.getDocuments().add(document);
        }
        StudentCourseOutlineVO outline = new StudentCourseOutlineVO();
        outline.setCourseId(courseId);
        outline.setKnowledgeBaseVersionId(context.getPublishedVersionId());
        outline.setVersionNo(context.getPublishedVersionNo());
        outline.setModules(new ArrayList<>(grouped.values()));
        return outline;
    }

    @Override
    public List<StudentPublishedDocumentVO> selectDocuments(
            Long courseId, Long userId, StudentDocumentQuery query)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        normalizeQuery(query);
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        return contentMapper.selectPublishedDocuments(
                context.getTenantId(), courseId, context.getPublishedVersionId(), query);
    }

    @Override
    public StudentPublishedDocumentVO selectDocument(Long courseId, Long documentId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        StudentPublishedDocumentVO document = contentMapper.selectPublishedDocument(
                context.getTenantId(), courseId, context.getPublishedVersionId(), documentId);
        if (document == null)
        {
            throw new ServiceException("资料不存在或未在当前课程版本发布");
        }
        return document;
    }

    @Override
    public CourseDocumentVersion selectPublishedVersion(Long courseId, Long documentId, Long userId)
    {
        StudentPublishedDocumentVO document = selectDocument(courseId, documentId, userId);
        return documentService.selectVersion(courseId, documentId, document.getDocumentVersionId());
    }

    @Override
    public boolean isDownloadAllowed(Long courseId, Long userId)
    {
        courseAccessService.requireStudentAccess(courseId, userId);
        Course course = courseMapper.selectCourseById(courseId);
        return course != null && Boolean.TRUE.equals(course.getAllowDownload());
    }

    @Override
    public java.io.InputStream openPublishedVersionStream(CourseDocumentVersion version)
    {
        return documentService.openVersionStream(version);
    }

    private StudentCourseContext requirePublishedContext(Long courseId, Long userId)
    {
        StudentCourseContext context = courseAccessService.requireStudentAccess(courseId, userId);
        if (context.getPublishedVersionId() == null)
        {
            throw new ServiceException("当前课程内容尚未发布");
        }
        return context;
    }

    private StudentCourseModuleVO createModule(StudentPublishedDocumentVO document)
    {
        StudentCourseModuleVO module = new StudentCourseModuleVO();
        module.setModuleId(document.getModuleId());
        module.setModuleCode(document.getModuleId() == null ? null : document.getModuleCode());
        module.setModuleName(document.getModuleId() == null ? "通用资料" : document.getModuleName());
        module.setDescription(document.getModuleId() == null ? "适用于本课程的通用资料" : document.getModuleDescription());
        module.setSortOrder(document.getModuleId() == null ? -1 : document.getModuleSortOrder());
        return module;
    }

    private void normalizeQuery(StudentDocumentQuery query)
    {
        if (query.getPageNum() == null || query.getPageNum() < 1)
        {
            query.setPageNum(1);
        }
        if (query.getPageSize() == null || query.getPageSize() < 1)
        {
            query.setPageSize(10);
        }
        else if (query.getPageSize() > 100)
        {
            query.setPageSize(100);
        }
        query.setKeyword(StringUtils.trimToNull(query.getKeyword()));
        query.setFileExt(StringUtils.trimToNull(query.getFileExt()));
    }
}
