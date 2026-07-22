package com.hezal.system.mapper;

import java.util.List;
import org.apache.ibatis.annotations.Param;
import com.hezal.system.domain.CourseUser;
import com.hezal.system.domain.vo.student.StudentCourseContext;
import com.hezal.system.domain.vo.student.StudentCourseVO;

/** 课程直接授权数据访问。 */
public interface CourseUserMapper
{
    List<CourseUser> selectByCourseId(Long courseId);
    CourseUser selectById(@Param("courseId") Long courseId, @Param("id") Long id);
    CourseUser selectByUserId(@Param("courseId") Long courseId, @Param("userId") Long userId);
    CourseUser selectEffectiveAccess(@Param("courseId") Long courseId, @Param("userId") Long userId);
    List<StudentCourseVO> selectStudentCourses(@Param("tenantId") Long tenantId, @Param("userId") Long userId);
    StudentCourseVO selectStudentCourse(@Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId, @Param("userId") Long userId);
    StudentCourseContext selectStudentCourseContext(@Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId, @Param("userId") Long userId);
    int insertCourseUser(CourseUser courseUser);
    int updateCourseUser(CourseUser courseUser);
    int deleteCourseUser(@Param("id") Long id, @Param("username") String username);
}
