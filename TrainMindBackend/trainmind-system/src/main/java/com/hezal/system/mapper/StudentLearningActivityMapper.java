package com.hezal.system.mapper;

import java.util.List;
import org.apache.ibatis.annotations.Param;
import com.hezal.system.domain.StudentLearningActivity;

/** 学员课程活动持久化。 */
public interface StudentLearningActivityMapper
{
    List<StudentLearningActivity> selectActivities(@Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId, @Param("userId") Long userId);

    int insertDeduplicated(StudentLearningActivity activity);
}
