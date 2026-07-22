package com.hezal.web.controller.student;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.system.service.IStudentCourseService;

/** 学员端课程入口。 */
@RestController
@RequestMapping("/student/courses")
public class StudentCourseController extends BaseController
{
    private final IStudentCourseService studentCourseService;

    public StudentCourseController(IStudentCourseService studentCourseService)
    {
        this.studentCourseService = studentCourseService;
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping
    public AjaxResult list()
    {
        return success(studentCourseService.selectMyCourses(getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/{courseId}")
    public AjaxResult getInfo(@PathVariable Long courseId)
    {
        return success(studentCourseService.selectMyCourse(courseId, getUserId()));
    }
}
