package com.hezal.system.service.impl;

import java.util.List;
import org.springframework.stereotype.Service;
import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.vo.student.StudentCourseVO;
import com.hezal.system.mapper.CourseUserMapper;
import com.hezal.system.service.IStudentCourseService;

/** 学员端课程只读服务实现。 */
@Service
public class StudentCourseServiceImpl implements IStudentCourseService
{
    private final CourseUserMapper courseUserMapper;

    public StudentCourseServiceImpl(CourseUserMapper courseUserMapper)
    {
        this.courseUserMapper = courseUserMapper;
    }

    @Override
    public List<StudentCourseVO> selectMyCourses(Long userId)
    {
        return courseUserMapper.selectStudentCourses(TrainMindConstants.DEFAULT_TENANT_ID, userId);
    }

    @Override
    public StudentCourseVO selectMyCourse(Long courseId, Long userId)
    {
        StudentCourseVO course = courseUserMapper.selectStudentCourse(
                TrainMindConstants.DEFAULT_TENANT_ID, courseId, userId);
        if (course == null)
        {
            throw new ServiceException("课程不存在或未向当前学员授权");
        }
        return course;
    }
}
