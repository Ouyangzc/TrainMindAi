package com.hezal.system.service;

import org.springframework.stereotype.Service;
import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.common.utils.SecurityUtils;
import com.hezal.system.domain.CourseUser;
import com.hezal.system.mapper.CourseUserMapper;

/** 课程级数据访问校验。 */
@Service
public class CourseAccessService
{
    private final CourseUserMapper courseUserMapper;

    public CourseAccessService(CourseUserMapper courseUserMapper)
    {
        this.courseUserMapper = courseUserMapper;
    }

    public CourseUser requireAccess(Long courseId, Long userId)
    {
        if (SecurityUtils.isAdmin(userId))
        {
            return null;
        }
        CourseUser access = courseUserMapper.selectEffectiveAccess(courseId, userId);
        if (access == null)
        {
            throw new ServiceException("无权访问当前课程");
        }
        return access;
    }

    public void requireManageAccess(Long courseId, Long userId)
    {
        CourseUser access = requireAccess(courseId, userId);
        if (access != null
                && !TrainMindConstants.COURSE_ACCESS_ROLE_OWNER.equals(access.getAccessRole())
                && !TrainMindConstants.COURSE_ACCESS_ROLE_TEACHER.equals(access.getAccessRole()))
        {
            throw new ServiceException("无权管理当前课程");
        }
    }

    public void requireOwnerAccess(Long courseId, Long userId)
    {
        CourseUser access = requireAccess(courseId, userId);
        if (access != null
                && !TrainMindConstants.COURSE_ACCESS_ROLE_OWNER.equals(access.getAccessRole()))
        {
            throw new ServiceException("只有课程主负责人可以管理课程成员");
        }
    }
}
