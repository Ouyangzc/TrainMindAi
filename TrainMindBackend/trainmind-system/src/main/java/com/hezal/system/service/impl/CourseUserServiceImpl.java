package com.hezal.system.service.impl;

import java.util.List;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.Course;
import com.hezal.system.domain.CourseUser;
import com.hezal.system.mapper.CourseMapper;
import com.hezal.system.mapper.CourseUserMapper;
import com.hezal.system.service.ICourseUserService;
import com.hezal.system.service.CourseAccessService;
import com.hezal.common.utils.SecurityUtils;

/** 课程成员直接授权服务实现。 */
@Service
public class CourseUserServiceImpl implements ICourseUserService
{
    private static final Set<String> EDITABLE_ROLES = Set.of(
            TrainMindConstants.COURSE_ACCESS_ROLE_TEACHER,
            TrainMindConstants.COURSE_ACCESS_ROLE_STUDENT);
    private static final Set<String> ACCESS_STATUSES = Set.of(
            TrainMindConstants.COURSE_ACCESS_STATUS_ACTIVE,
            TrainMindConstants.COURSE_ACCESS_STATUS_DISABLED);

    private final CourseUserMapper courseUserMapper;
    private final CourseMapper courseMapper;
    private final CourseAccessService courseAccessService;

    public CourseUserServiceImpl(CourseUserMapper courseUserMapper, CourseMapper courseMapper,
            CourseAccessService courseAccessService)
    {
        this.courseUserMapper = courseUserMapper;
        this.courseMapper = courseMapper;
        this.courseAccessService = courseAccessService;
    }

    @Override
    public List<CourseUser> selectMembers(Long courseId)
    {
        courseAccessService.requireOwnerAccess(courseId, SecurityUtils.getUserId());
        requireCourse(courseId);
        return courseUserMapper.selectByCourseId(courseId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CourseUser addMember(Long courseId, CourseUser member, String username)
    {
        courseAccessService.requireOwnerAccess(courseId, SecurityUtils.getUserId());
        Course course = requireCourse(courseId);
        validateEditableMember(member);
        if (member.getUserId() == null)
        {
            throw new ServiceException("用户ID不能为空");
        }
        if (courseUserMapper.selectByUserId(courseId, member.getUserId()) != null)
        {
            throw new ServiceException("该用户已是课程成员");
        }
        member.setTenantId(course.getTenantId());
        member.setCourseId(courseId);
        member.setCreateBy(username);
        courseUserMapper.insertCourseUser(member);
        return courseUserMapper.selectById(courseId, member.getId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CourseUser updateMember(
            Long courseId, Long memberId, CourseUser member, String username)
    {
        courseAccessService.requireOwnerAccess(courseId, SecurityUtils.getUserId());
        CourseUser existing = requireMember(courseId, memberId);
        requireNotOwner(existing);
        validateEditableMember(member);
        member.setId(memberId);
        member.setUpdateBy(username);
        courseUserMapper.updateCourseUser(member);
        return courseUserMapper.selectById(courseId, memberId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int deleteMember(Long courseId, Long memberId, String username)
    {
        courseAccessService.requireOwnerAccess(courseId, SecurityUtils.getUserId());
        CourseUser existing = requireMember(courseId, memberId);
        requireNotOwner(existing);
        return courseUserMapper.deleteCourseUser(memberId, username);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CourseUser transferOwner(Long courseId, Long targetUserId, String username)
    {
        courseAccessService.requireOwnerAccess(courseId, SecurityUtils.getUserId());
        if (targetUserId == null)
        {
            throw new ServiceException("目标负责人不能为空");
        }
        Course course = courseMapper.lockCourseById(courseId);
        if (course == null)
        {
            throw new ServiceException("课程不存在");
        }
        if (targetUserId.equals(course.getOwnerUserId()))
        {
            throw new ServiceException("目标用户已是课程主负责人");
        }

        CourseUser oldOwner = course.getOwnerUserId() == null ? null
                : courseUserMapper.selectByUserId(courseId, course.getOwnerUserId());
        if (oldOwner != null)
        {
            oldOwner.setAccessRole(TrainMindConstants.COURSE_ACCESS_ROLE_TEACHER);
            oldOwner.setAccessStatus(TrainMindConstants.COURSE_ACCESS_STATUS_ACTIVE);
            oldOwner.setUpdateBy(username);
            courseUserMapper.updateCourseUser(oldOwner);
        }

        CourseUser target = courseUserMapper.selectByUserId(courseId, targetUserId);
        if (target == null)
        {
            target = new CourseUser();
            target.setTenantId(course.getTenantId());
            target.setCourseId(courseId);
            target.setUserId(targetUserId);
            target.setAccessRole(TrainMindConstants.COURSE_ACCESS_ROLE_OWNER);
            target.setAccessStatus(TrainMindConstants.COURSE_ACCESS_STATUS_ACTIVE);
            target.setCreateBy(username);
            courseUserMapper.insertCourseUser(target);
        }
        else
        {
            target.setAccessRole(TrainMindConstants.COURSE_ACCESS_ROLE_OWNER);
            target.setAccessStatus(TrainMindConstants.COURSE_ACCESS_STATUS_ACTIVE);
            target.setUpdateBy(username);
            courseUserMapper.updateCourseUser(target);
        }

        Course update = new Course();
        update.setId(courseId);
        update.setOwnerUserId(targetUserId);
        update.setUpdateBy(username);
        courseMapper.updateCourse(update);
        return courseUserMapper.selectByUserId(courseId, targetUserId);
    }

    private Course requireCourse(Long courseId)
    {
        Course course = courseMapper.selectCourseById(courseId);
        if (course == null)
        {
            throw new ServiceException("课程不存在");
        }
        return course;
    }

    private CourseUser requireMember(Long courseId, Long memberId)
    {
        CourseUser member = courseUserMapper.selectById(courseId, memberId);
        if (member == null)
        {
            throw new ServiceException("课程成员不存在");
        }
        return member;
    }

    private void requireNotOwner(CourseUser member)
    {
        if (TrainMindConstants.COURSE_ACCESS_ROLE_OWNER.equals(member.getAccessRole()))
        {
            throw new ServiceException("主负责人只能通过负责人转移接口变更");
        }
    }

    private void validateEditableMember(CourseUser member)
    {
        if (!EDITABLE_ROLES.contains(member.getAccessRole()))
        {
            throw new ServiceException("普通成员角色只能是 teacher 或 student");
        }
        if (!ACCESS_STATUSES.contains(member.getAccessStatus()))
        {
            throw new ServiceException("课程授权状态无效");
        }
        if (member.getStartAt() != null && member.getEndAt() != null
                && member.getEndAt().before(member.getStartAt()))
        {
            throw new ServiceException("授权结束时间不能早于开始时间");
        }
    }
}
