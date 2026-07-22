package com.hezal.system.service.impl;

import java.util.List;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.StudentLearningActivity;
import com.hezal.system.domain.vo.student.StudentCourseContext;
import com.hezal.system.domain.vo.student.StudentPublishedDocumentVO;
import com.hezal.system.mapper.StudentLearningActivityMapper;
import com.hezal.system.mapper.StudentPublishedContentMapper;
import com.hezal.system.service.CourseAccessService;
import com.hezal.system.service.IStudentLearningActivityService;

/** 学员课程事实活动服务实现。 */
@Service
public class StudentLearningActivityServiceImpl implements IStudentLearningActivityService
{
    private final CourseAccessService courseAccessService;
    private final StudentPublishedContentMapper contentMapper;
    private final StudentLearningActivityMapper activityMapper;

    public StudentLearningActivityServiceImpl(CourseAccessService courseAccessService,
            StudentPublishedContentMapper contentMapper, StudentLearningActivityMapper activityMapper)
    {
        this.courseAccessService = courseAccessService;
        this.contentMapper = contentMapper;
        this.activityMapper = activityMapper;
    }

    @Override
    public List<StudentLearningActivity> selectActivities(Long courseId, Long userId)
    {
        StudentCourseContext context = courseAccessService.requireStudentAccess(courseId, userId);
        return activityMapper.selectActivities(context.getTenantId(), courseId, userId);
    }

    @Override
    public void record(Long courseId, Long userId, String activityType, Long targetId)
    {
        StudentCourseContext context = courseAccessService.requireStudentAccess(courseId, userId);
        StudentLearningActivity activity = baseActivity(context, courseId, userId, activityType, targetId);
        if ("course_view".equals(activityType))
        {
            activity.setTargetId(courseId);
            activity.setTargetTitle("进入课程空间");
        }
        else if ("document_view".equals(activityType))
        {
            requirePublished(context);
            StudentPublishedDocumentVO document = contentMapper.selectPublishedDocument(
                    context.getTenantId(), courseId, context.getPublishedVersionId(), targetId);
            if (document == null)
            {
                throw new ServiceException("资料不存在或未在当前课程版本发布");
            }
            activity.setTargetTitle(document.getTitle());
            activity.setTargetDetail(document.getOriginalFilename());
        }
        else if ("module_view".equals(activityType))
        {
            if (targetId == null)
            {
                throw new ServiceException("模块不能为空");
            }
            requirePublished(context);
            String moduleName = contentMapper.selectPublishedModuleName(
                    context.getTenantId(), courseId, context.getPublishedVersionId(), targetId);
            if (moduleName == null)
            {
                throw new ServiceException("模块不存在或未在当前课程版本发布");
            }
            activity.setTargetTitle(moduleName);
        }
        else
        {
            throw new ServiceException("不支持的活动类型");
        }
        activityMapper.insertDeduplicated(activity);
    }

    @Override
    public void recordChat(Long courseId, Long userId, Long sessionId, String question)
    {
        StudentCourseContext context = courseAccessService.requireStudentAccess(courseId, userId);
        StudentLearningActivity activity = baseActivity(
                context, courseId, userId, "chat", sessionId);
        activity.setTargetTitle("向 AI 学习助教提问");
        activity.setTargetDetail(StringUtils.abbreviate(question, 120));
        activityMapper.insertDeduplicated(activity);
    }

    private StudentLearningActivity baseActivity(StudentCourseContext context, Long courseId,
            Long userId, String activityType, Long targetId)
    {
        StudentLearningActivity activity = new StudentLearningActivity();
        activity.setTenantId(context.getTenantId());
        activity.setUserId(userId);
        activity.setCourseId(courseId);
        activity.setActivityType(activityType);
        activity.setTargetId(targetId);
        activity.setCreateBy(userId.toString());
        return activity;
    }

    private void requirePublished(StudentCourseContext context)
    {
        if (context.getPublishedVersionId() == null)
        {
            throw new ServiceException("当前课程内容尚未发布");
        }
    }
}
