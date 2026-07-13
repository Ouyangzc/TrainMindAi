package com.hezal.system.service;

import java.util.List;

import com.hezal.system.domain.Course;

/**
 * 课程服务接口。
 *
 * @author trainmind
 */
public interface ICourseService
{
    List<Course> selectCourseList(Course course);

    Course selectCourseById(Long id);

    int insertCourse(Course course);

    int updateCourse(Course course);

    int deleteCourseByIds(Long[] ids);

    boolean checkCourseCodeUnique(Course course);
}
