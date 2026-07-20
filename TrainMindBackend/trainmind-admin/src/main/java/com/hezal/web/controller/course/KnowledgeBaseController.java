package com.hezal.web.controller.course;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.hezal.common.annotation.Log;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.common.enums.BusinessType;
import com.hezal.system.domain.dto.KnowledgeBaseSnapshotRequest;
import com.hezal.system.service.IKnowledgeBaseService;
import com.hezal.system.service.CourseAccessService;

/** 课程知识库治理。 */
@RestController
@RequestMapping("/course/{courseId}/knowledge-base")
public class KnowledgeBaseController extends BaseController
{
    private final IKnowledgeBaseService knowledgeBaseService;
    private final CourseAccessService courseAccessService;

    public KnowledgeBaseController(IKnowledgeBaseService knowledgeBaseService,
            CourseAccessService courseAccessService)
    {
        this.knowledgeBaseService = knowledgeBaseService;
        this.courseAccessService = courseAccessService;
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:query')")
    @GetMapping
    public AjaxResult getInfo(@PathVariable Long courseId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.selectKnowledgeBase(courseId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:query')")
    @GetMapping("/versions")
    public AjaxResult versions(@PathVariable Long courseId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.selectVersions(courseId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:edit')")
    @Log(title = "知识库草稿", businessType = BusinessType.INSERT)
    @PostMapping("/versions")
    public AjaxResult createDraft(@PathVariable Long courseId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.createDraft(courseId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:query')")
    @GetMapping("/versions/{versionId}/documents")
    public AjaxResult snapshot(@PathVariable Long courseId, @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.selectSnapshot(courseId, versionId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:edit')")
    @Log(title = "知识库资料快照", businessType = BusinessType.UPDATE)
    @PutMapping("/versions/{versionId}/documents")
    public AjaxResult saveSnapshot(@PathVariable Long courseId, @PathVariable Long versionId,
            @RequestBody KnowledgeBaseSnapshotRequest request)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.saveSnapshot(
                courseId, versionId, request.getDocumentVersionIds(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:build')")
    @Log(title = "知识库构建", businessType = BusinessType.UPDATE)
    @PostMapping("/versions/{versionId}/build")
    public AjaxResult build(@PathVariable Long courseId, @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.build(courseId, versionId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:query')")
    @GetMapping("/versions/{versionId}/build-status")
    public AjaxResult buildStatus(@PathVariable Long courseId, @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.selectBuildStatus(courseId, versionId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:publish')")
    @Log(title = "知识库发布", businessType = BusinessType.UPDATE)
    @PostMapping("/versions/{versionId}/publish")
    public AjaxResult publish(@PathVariable Long courseId, @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.publish(courseId, versionId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:knowledge-base:publish')")
    @Log(title = "知识库回滚", businessType = BusinessType.INSERT)
    @PostMapping("/versions/{versionId}/rollback")
    public AjaxResult rollback(@PathVariable Long courseId, @PathVariable Long versionId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(knowledgeBaseService.rollback(courseId, versionId, getUsername()));
    }
}
