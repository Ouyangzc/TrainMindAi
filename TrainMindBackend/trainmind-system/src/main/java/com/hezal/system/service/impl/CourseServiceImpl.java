package com.hezal.system.service.impl;

import java.util.List;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.Course;
import com.hezal.system.domain.KnowledgeBase;
import com.hezal.system.domain.CourseUser;
import com.hezal.system.mapper.CourseMapper;
import com.hezal.system.mapper.CourseUserMapper;
import com.hezal.system.mapper.KnowledgeBaseMapper;
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
    private final KnowledgeBaseMapper knowledgeBaseMapper;
    private final CourseUserMapper courseUserMapper;

    public CourseServiceImpl(CourseMapper courseMapper, KnowledgeBaseMapper knowledgeBaseMapper,
            CourseUserMapper courseUserMapper)
    {
        this.courseMapper = courseMapper;
        this.knowledgeBaseMapper = knowledgeBaseMapper;
        this.courseUserMapper = courseUserMapper;
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
    @Transactional(rollbackFor = Exception.class)
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
        if (course.getAllowDownload() == null)
        {
            course.setAllowDownload(false);
        }
        int rows = courseMapper.insertCourse(course);
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setTenantId(course.getTenantId());
        knowledgeBase.setCourseId(course.getId());
        knowledgeBase.setName(course.getCourseName() + "知识库");
        knowledgeBase.setDescription(course.getDescription());
        knowledgeBase.setStatus(TrainMindConstants.KNOWLEDGE_BASE_STATUS_ACTIVE);
        knowledgeBase.setCreateBy(course.getCreateBy());
        knowledgeBaseMapper.insertKnowledgeBase(knowledgeBase);
        CourseUser owner = new CourseUser();
        owner.setTenantId(course.getTenantId());
        owner.setCourseId(course.getId());
        owner.setUserId(course.getOwnerUserId());
        owner.setAccessRole(TrainMindConstants.COURSE_ACCESS_ROLE_OWNER);
        owner.setAccessStatus(TrainMindConstants.COURSE_ACCESS_STATUS_ACTIVE);
        owner.setCreateBy(course.getCreateBy());
        courseUserMapper.insertCourseUser(owner);
        return rows;
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
