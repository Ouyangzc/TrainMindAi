package com.hezal.web.controller.student;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.common.core.page.TableDataInfo;
import com.hezal.system.domain.dto.StudentDocumentQuery;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.vo.student.StudentPublishedDocumentVO;
import com.hezal.system.service.IStudentPublishedContentService;

/** 学员端当前发布课程目录与资料。 */
@RestController
@RequestMapping("/student/courses/{courseId}")
public class StudentPublishedContentController extends BaseController
{
    private final IStudentPublishedContentService contentService;

    public StudentPublishedContentController(IStudentPublishedContentService contentService)
    {
        this.contentService = contentService;
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/outline")
    public AjaxResult outline(@PathVariable Long courseId)
    {
        return success(contentService.selectOutline(courseId, getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/documents")
    public TableDataInfo documents(@PathVariable Long courseId, StudentDocumentQuery query)
    {
        List<StudentPublishedDocumentVO> documents = contentService.selectDocuments(
                courseId, getUserId(), query);
        return getDataTable(documents);
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/documents/{documentId}")
    public AjaxResult document(@PathVariable Long courseId, @PathVariable Long documentId)
    {
        return success(contentService.selectDocument(courseId, documentId, getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/documents/{documentId}/preview")
    public void preview(@PathVariable Long courseId, @PathVariable Long documentId,
            HttpServletResponse response) throws Exception
    {
        CourseDocumentVersion version = contentService.selectPublishedVersion(courseId, documentId, getUserId());
        if (!"pdf".equalsIgnoreCase(version.getFileExt()))
        {
            response.setStatus(HttpServletResponse.SC_UNSUPPORTED_MEDIA_TYPE);
            return;
        }
        stream(version, response, false);
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/documents/{documentId}/download")
    public void download(@PathVariable Long courseId, @PathVariable Long documentId,
            HttpServletResponse response) throws Exception
    {
        if (!contentService.isDownloadAllowed(courseId, getUserId()))
        {
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            return;
        }
        CourseDocumentVersion version = contentService.selectPublishedVersion(courseId, documentId, getUserId());
        stream(version, response, true);
    }

    private void stream(CourseDocumentVersion version, HttpServletResponse response,
            boolean attachment) throws Exception
    {
        response.setContentType(StringUtils.defaultIfEmpty(version.getContentType(), "application/octet-stream"));
        response.setContentLengthLong(version.getFileSize());
        ContentDisposition disposition = (attachment ? ContentDisposition.attachment() : ContentDisposition.inline())
                .filename(version.getOriginalFilename(), StandardCharsets.UTF_8)
                .build();
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, disposition.toString());
        response.setHeader(HttpHeaders.CACHE_CONTROL, "private, no-store");
        try (InputStream input = contentService.openPublishedVersionStream(version))
        {
            IOUtils.copy(input, response.getOutputStream());
        }
    }
}
