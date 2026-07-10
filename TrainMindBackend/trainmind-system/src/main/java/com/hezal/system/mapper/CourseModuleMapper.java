package com.hezal.system.mapper;

import java.util.List;

import com.hezal.system.domain.CourseModule;

/**
 * 课程模块Mapper接口。
 *
 * @author trainmind
 */
public interface CourseModuleMapper
{
    List<CourseModule> selectCourseModuleList(CourseModule module);

    CourseModule selectCourseModuleById(Long id);

    int insertCourseModule(CourseModule module);

    int updateCourseModule(CourseModule module);

    int deleteCourseModuleById(Long id);
}
