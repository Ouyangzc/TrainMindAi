package com.hezal.web.controller.course;

import java.io.InputStream;
import java.util.List;

import jakarta.servlet.http.HttpServletResponse;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.hezal.common.annotation.Log;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.common.enums.BusinessType;
import com.hezal.common.utils.file.FileUtils;
import com.hezal.system.domain.CourseDocument;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.service.ICourseDocumentService;
import com.hezal.system.service.CourseAccessService;

/**
 * 课程资料管理。
 *
 * @author trainmind
 */
@RestController
@RequestMapping("/course/{courseId}/documents")
public class CourseDocumentController extends BaseController
{
    private final ICourseDocumentService documentService;
    private final CourseAccessService courseAccessService;

    public CourseDocumentController(ICourseDocumentService documentService,
            CourseAccessService courseAccessService)
    {
        this.documentService = documentService;
        this.courseAccessService = courseAccessService;
    }

    @PreAuthorize("@ss.hasPermi('course:document:list')")
    @GetMapping
    public AjaxResult list(@PathVariable Long courseId, CourseDocument document)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        document.setCourseId(courseId);
        List<CourseDocument> list = documentService.selectCourseDocumentList(document);
        return success(list);
    }

    @PreAuthorize("@ss.hasPermi('course:document:upload')")
    @Log(title = "课程资料", businessType = BusinessType.INSERT)
    @PostMapping("/upload")
    public AjaxResult upload(@PathVariable Long courseId,
            @RequestParam(required = false) Long moduleId,
            @RequestParam String title,
            @RequestParam(required = false) String remark,
            @RequestParam MultipartFile file)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(documentService.uploadDocument(courseId, moduleId, title, remark, file, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:document:upload')")
    @Log(title = "课程资料版本", businessType = BusinessType.INSERT)
    @PostMapping("/{documentId}/versions")
    public AjaxResult uploadVersion(@PathVariable Long courseId, @PathVariable Long documentId,
            @RequestParam(required = false) String remark, @RequestParam MultipartFile file)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(documentService.uploadVersion(courseId, documentId, remark, file, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:document:query')")
    @GetMapping("/{documentId}/versions")
    public AjaxResult versions(@PathVariable Long courseId, @PathVariable Long documentId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(documentService.selectVersions(courseId, documentId));
    }

    @PreAuthorize("@ss.hasPermi('course:document:download')")
    @GetMapping("/{documentId}/versions/{versionId}/download")
    public void download(@PathVariable Long courseId, @PathVariable Long documentId,
            @PathVariable Long versionId, HttpServletResponse response) throws Exception
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        CourseDocumentVersion version = documentService.selectVersion(courseId, documentId, versionId);
        response.setContentType(StringUtils.defaultIfEmpty(version.getContentType(), "application/octet-stream"));
        response.setContentLengthLong(version.getFileSize());
        FileUtils.setAttachmentResponseHeader(response, version.getOriginalFilename());
        try (InputStream input = documentService.openVersionStream(version))
        {
            IOUtils.copy(input, response.getOutputStream());
        }
    }

    @PreAuthorize("@ss.hasPermi('course:document:parse')")
    @Log(title = "课程资料解析", businessType = BusinessType.UPDATE)
    @PostMapping("/{documentId}/versions/{versionId}/parse")
    public AjaxResult parse(@PathVariable Long courseId, @PathVariable Long documentId,
            @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(documentService.triggerParse(courseId, documentId, versionId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:document:query')")
    @GetMapping("/{documentId}/versions/{versionId}/parse-task")
    public AjaxResult parseTask(@PathVariable Long courseId, @PathVariable Long documentId,
            @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(documentService.selectParseTask(
                courseId, documentId, versionId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:document:remove')")
    @Log(title = "课程资料", businessType = BusinessType.DELETE)
    @DeleteMapping("/{documentId}")
    public AjaxResult remove(@PathVariable Long courseId, @PathVariable Long documentId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return toAjax(documentService.deleteCourseDocument(courseId, documentId));
    }
}
