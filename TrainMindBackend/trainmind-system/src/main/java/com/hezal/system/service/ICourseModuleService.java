package com.hezal.system.service;

import java.util.List;

import com.hezal.system.domain.CourseModule;

/**
 * 课程模块服务接口。
 *
 * @author trainmind
 */
public interface ICourseModuleService
{
    List<CourseModule> selectCourseModuleList(CourseModule module);

    CourseModule selectCourseModuleById(Long id);

    int insertCourseModule(CourseModule module);

    int updateCourseModule(CourseModule module);

    int deleteCourseModuleById(Long id);
}
