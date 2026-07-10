package com.hezal.system.service.impl;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.hezal.common.constant.TrainMindConstants;
import com.hezal.system.domain.CourseModule;
import com.hezal.system.mapper.CourseModuleMapper;
import com.hezal.system.service.ICourseModuleService;

/**
 * 课程模块服务实现。
 *
 * @author trainmind
 */
@Service
public class CourseModuleServiceImpl implements ICourseModuleService
{
    @Autowired
    private CourseModuleMapper courseModuleMapper;

    @Override
    public List<CourseModule> selectCourseModuleList(CourseModule module)
    {
        applyDefaultTenant(module);
        return courseModuleMapper.selectCourseModuleList(module);
    }

    @Override
    public CourseModule selectCourseModuleById(Long id)
    {
        return courseModuleMapper.selectCourseModuleById(id);
    }

    @Override
    public int insertCourseModule(CourseModule module)
    {
        applyDefaultTenant(module);
        if (module.getStatus() == null || module.getStatus().isEmpty())
        {
            module.setStatus("active");
        }
        return courseModuleMapper.insertCourseModule(module);
    }

    @Override
    public int updateCourseModule(CourseModule module)
    {
        return courseModuleMapper.updateCourseModule(module);
    }

    @Override
    public int deleteCourseModuleById(Long id)
    {
        return courseModuleMapper.deleteCourseModuleById(id);
    }

    private void applyDefaultTenant(CourseModule module)
    {
        if (module != null && module.getTenantId() == null)
        {
            module.setTenantId(TrainMindConstants.DEFAULT_TENANT_ID);
        }
    }
}
