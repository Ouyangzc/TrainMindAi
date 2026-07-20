package com.hezal.system.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Param;

import com.hezal.system.domain.Course;

/**
 * 课程Mapper接口。
 *
 * @author trainmind
 */
public interface CourseMapper
{
    List<Course> selectCourseList(Course course);

    Course selectCourseById(Long id);
    Course lockCourseById(Long id);

    Course selectCourseByCode(@Param("tenantId") Long tenantId, @Param("courseCode") String courseCode);

    int insertCourse(Course course);

    int updateCourse(Course course);

    int deleteCourseById(Long id);

    int countChildren(Long id);
}
