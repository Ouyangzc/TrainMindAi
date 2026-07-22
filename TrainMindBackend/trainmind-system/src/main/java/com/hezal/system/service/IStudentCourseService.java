package com.hezal.system.service;

import java.util.List;
import com.hezal.system.domain.vo.student.StudentCourseVO;

/** 学员端课程只读服务。 */
public interface IStudentCourseService
{
    List<StudentCourseVO> selectMyCourses(Long userId);

    StudentCourseVO selectMyCourse(Long courseId, Long userId);
}
