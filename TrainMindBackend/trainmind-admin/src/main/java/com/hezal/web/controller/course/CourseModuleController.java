package com.hezal.web.controller.course;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
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
import com.hezal.common.enums.BusinessType;
import com.hezal.system.domain.CourseModule;
import com.hezal.system.service.ICourseModuleService;
import com.hezal.system.service.CourseAccessService;

/**
 * 课程模块管理。
 *
 * @author trainmind
 */
@RestController
@RequestMapping("/course/{courseId}/modules")
public class CourseModuleController extends BaseController
{
    @Autowired
    private ICourseModuleService courseModuleService;
    @Autowired
    private CourseAccessService courseAccessService;

    /**
     * 查询课程模块列表。
     */
    @PreAuthorize("@ss.hasPermi('course:module:list')")
    @GetMapping
    public AjaxResult list(@PathVariable Long courseId, CourseModule module)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        module.setCourseId(courseId);
        List<CourseModule> list = courseModuleService.selectCourseModuleList(module);
        return success(list);
    }

    /**
     * 查询课程模块详情。
     */
    @PreAuthorize("@ss.hasPermi('course:module:query')")
    @GetMapping("/{moduleId}")
    public AjaxResult getInfo(@PathVariable Long courseId, @PathVariable Long moduleId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return success(courseModuleService.selectCourseModuleById(moduleId));
    }

    /**
     * 新增课程模块。
     */
    @PreAuthorize("@ss.hasPermi('course:module:add')")
    @Log(title = "课程模块", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@PathVariable Long courseId, @Validated @RequestBody CourseModule module)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        module.setCourseId(courseId);
        module.setCreateBy(getUsername());
        return toAjax(courseModuleService.insertCourseModule(module));
    }

    /**
     * 修改课程模块。
     */
    @PreAuthorize("@ss.hasPermi('course:module:edit')")
    @Log(title = "课程模块", businessType = BusinessType.UPDATE)
    @PutMapping("/{moduleId}")
    public AjaxResult edit(@PathVariable Long courseId, @PathVariable Long moduleId,
            @Validated @RequestBody CourseModule module)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        module.setId(moduleId);
        module.setCourseId(courseId);
        module.setUpdateBy(getUsername());
        return toAjax(courseModuleService.updateCourseModule(module));
    }

    /**
     * 删除课程模块。
     */
    @PreAuthorize("@ss.hasPermi('course:module:remove')")
    @Log(title = "课程模块", businessType = BusinessType.DELETE)
    @DeleteMapping("/{moduleId}")
    public AjaxResult remove(@PathVariable Long courseId, @PathVariable Long moduleId)
    {
        courseAccessService.requireManageAccess(courseId, getUserId());
        return toAjax(courseModuleService.deleteCourseModuleById(moduleId));
    }
}
