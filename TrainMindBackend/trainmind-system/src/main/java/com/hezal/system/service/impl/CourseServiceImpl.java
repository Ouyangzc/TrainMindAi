package com.hezal.system.service.impl;

import java.util.List;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.Course;
import com.hezal.system.mapper.CourseMapper;
import com.hezal.system.service.ICourseService;

/**
 * 课程服务实现。
 *
 * @author trainmind
 */
@Service
public class CourseServiceImpl implements ICourseService
{
    private final CourseMapper courseMapper;

    public CourseServiceImpl(CourseMapper courseMapper)
    {
        this.courseMapper = courseMapper;
    }

    @Override
    public List<Course> selectCourseList(Course course)
    {
        applyDefaultTenant(course);
        return courseMapper.selectCourseList(course);
    }

    @Override
    public Course selectCourseById(Long id)
    {
        return courseMapper.selectCourseById(id);
    }

    @Override
    public int insertCourse(Course course)
    {
        applyDefaultTenant(course);
        if (StringUtils.isBlank(course.getStatus()))
        {
            course.setStatus(TrainMindConstants.COURSE_STATUS_ACTIVE);
        }
        if (course.getSortOrder() == null)
        {
            course.setSortOrder(0);
        }
        return courseMapper.insertCourse(course);
    }

    @Override
    public int updateCourse(Course course)
    {
        return courseMapper.updateCourse(course);
    }

    @Override
    public int deleteCourseByIds(Long[] ids)
    {
        int rows = 0;
        for (Long id : ids)
        {
            if (courseMapper.countChildren(id) > 0)
            {
                throw new ServiceException("课程下存在模块或资料，不能删除");
            }
            rows += courseMapper.deleteCourseById(id);
        }
        return rows;
    }

    @Override
    public boolean checkCourseCodeUnique(Course course)
    {
        if (StringUtils.isBlank(course.getCourseCode()))
        {
            return true;
        }
        Long tenantId = course.getTenantId() == null ? TrainMindConstants.DEFAULT_TENANT_ID : course.getTenantId();
        Course exists = courseMapper.selectCourseByCode(tenantId, course.getCourseCode());
        return exists == null || exists.getId().equals(course.getId());
    }

    private void applyDefaultTenant(Course course)
    {
        if (course != null && course.getTenantId() == null)
        {
            course.setTenantId(TrainMindConstants.DEFAULT_TENANT_ID);
        }
    }
}
