package com.hezal.system.service;

import java.util.List;
import com.hezal.system.domain.StudentLearningActivity;

/** 学员课程事实活动服务。 */
public interface IStudentLearningActivityService
{
    List<StudentLearningActivity> selectActivities(Long courseId, Long userId);

    void record(Long courseId, Long userId, String activityType, Long targetId);

    void recordChat(Long courseId, Long userId, Long sessionId, String question);
}
