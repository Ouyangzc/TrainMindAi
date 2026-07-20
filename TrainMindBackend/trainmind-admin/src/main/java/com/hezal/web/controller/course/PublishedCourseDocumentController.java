package com.hezal.web.controller.course;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.system.service.IKnowledgeBaseService;

/** 学员当前发布资料。 */
@RestController
@RequestMapping("/course/{courseId}/published-documents")
public class PublishedCourseDocumentController extends BaseController
{
    private final IKnowledgeBaseService knowledgeBaseService;

    public PublishedCourseDocumentController(IKnowledgeBaseService knowledgeBaseService)
    {
        this.knowledgeBaseService = knowledgeBaseService;
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping
    public AjaxResult list(@PathVariable Long courseId)
    {
        return success(knowledgeBaseService.selectPublishedDocuments(courseId, getUserId()));
    }
}
