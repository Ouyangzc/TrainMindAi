package com.hezal.web.controller.course;

import org.springframework.security.access.prepost.PreAuthorize;
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
import com.hezal.system.domain.CourseUser;
import com.hezal.system.domain.dto.CourseOwnerTransferRequest;
import com.hezal.system.service.ICourseUserService;

/** 课程成员直接授权。 */
@RestController
@RequestMapping("/course/{courseId}")
public class CourseUserController extends BaseController
{
    private final ICourseUserService courseUserService;

    public CourseUserController(ICourseUserService courseUserService)
    {
        this.courseUserService = courseUserService;
    }

    @PreAuthorize("@ss.hasPermi('course:member:list')")
    @GetMapping("/members")
    public AjaxResult list(@PathVariable Long courseId)
    {
        return success(courseUserService.selectMembers(courseId));
    }

    @PreAuthorize("@ss.hasPermi('course:member:edit')")
    @Log(title = "课程成员", businessType = BusinessType.INSERT)
    @PostMapping("/members")
    public AjaxResult add(@PathVariable Long courseId, @RequestBody CourseUser member)
    {
        return success(courseUserService.addMember(courseId, member, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:member:edit')")
    @Log(title = "课程成员", businessType = BusinessType.UPDATE)
    @PutMapping("/members/{memberId}")
    public AjaxResult edit(@PathVariable Long courseId, @PathVariable Long memberId,
            @RequestBody CourseUser member)
    {
        return success(courseUserService.updateMember(courseId, memberId, member, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:member:edit')")
    @Log(title = "课程成员", businessType = BusinessType.DELETE)
    @DeleteMapping("/members/{memberId}")
    public AjaxResult remove(@PathVariable Long courseId, @PathVariable Long memberId)
    {
        return toAjax(courseUserService.deleteMember(courseId, memberId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('course:member:edit')")
    @Log(title = "课程负责人转移", businessType = BusinessType.UPDATE)
    @PutMapping("/owner/transfer")
    public AjaxResult transferOwner(@PathVariable Long courseId,
            @RequestBody CourseOwnerTransferRequest request)
    {
        return success(courseUserService.transferOwner(
                courseId, request.getTargetUserId(), getUsername()));
    }
}
