package com.hezal.web.controller.student;

import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.system.domain.dto.StudentActivityRequest;
import com.hezal.system.service.IStudentLearningActivityService;

/** 学员课程事实活动。 */
@RestController
@RequestMapping("/student/courses/{courseId}/activities")
public class StudentLearningActivityController extends BaseController
{
    private final IStudentLearningActivityService activityService;

    public StudentLearningActivityController(IStudentLearningActivityService activityService)
    {
        this.activityService = activityService;
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping
    public AjaxResult list(@PathVariable Long courseId)
    {
        return success(activityService.selectActivities(courseId, getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @PostMapping
    public AjaxResult record(@PathVariable Long courseId,
            @Valid @RequestBody StudentActivityRequest request)
    {
        activityService.record(courseId, getUserId(), request.getActivityType(), request.getTargetId());
        return success();
    }
}
