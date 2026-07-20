package com.hezal.web.controller.course;

import java.util.List;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
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
import com.hezal.common.core.page.TableDataInfo;
import com.hezal.common.enums.BusinessType;
import com.hezal.system.domain.Course;
import com.hezal.system.service.ICourseService;

/**
 * 课程管理。
 *
 * @author trainmind
 */
@RestController
@RequestMapping("/course")
public class CourseController extends BaseController
{
    private final ICourseService courseService;

    public CourseController(ICourseService courseService)
    {
        this.courseService = courseService;
    }

    /**
     * 查询课程列表。
     */
    @PreAuthorize("@ss.hasPermi('course:course:list')")
    @GetMapping("/list")
    public TableDataInfo list(Course course)
    {
        startPage();
        List<Course> list = courseService.selectCourseList(course);
        return getDataTable(list);
    }

    /**
     * 查询课程详情。
     */
    @PreAuthorize("@ss.hasPermi('course:course:query')")
    @GetMapping("/{courseId}")
    public AjaxResult getInfo(@PathVariable Long courseId)
    {
        return success(courseService.selectCourseById(courseId));
    }

    /**
     * 新增课程。
     */
    @PreAuthorize("@ss.hasPermi('course:course:add')")
    @Log(title = "课程管理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@Validated @RequestBody Course course)
    {
        if (!courseService.checkCourseCodeUnique(course))
        {
            return error("新增课程'" + course.getCourseName() + "'失败，课程编码已存在");
        }
        course.setCreateBy(getUsername());
        if (course.getOwnerUserId() == null)
        {
            course.setOwnerUserId(getUserId());
        }
        return toAjax(courseService.insertCourse(course));
    }

    /**
     * 修改课程。
     */
    @PreAuthorize("@ss.hasPermi('course:course:edit')")
    @Log(title = "课程管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@Validated @RequestBody Course course)
    {
        if (!courseService.checkCourseCodeUnique(course))
        {
            return error("修改课程'" + course.getCourseName() + "'失败，课程编码已存在");
        }
        course.setUpdateBy(getUsername());
        return toAjax(courseService.updateCourse(course));
    }

    /**
     * 删除课程。
     */
    @PreAuthorize("@ss.hasPermi('course:course:remove')")
    @Log(title = "课程管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{courseIds}")
    public AjaxResult remove(@PathVariable Long[] courseIds)
    {
        return toAjax(courseService.deleteCourseByIds(courseIds));
    }
}
