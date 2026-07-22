package com.hezal.system.mapper;

import java.util.List;
import org.apache.ibatis.annotations.Param;
import com.hezal.system.domain.StudentQaCitation;
import com.hezal.system.domain.StudentQaMessage;
import com.hezal.system.domain.StudentQaSession;

/** 学员课程问答持久化。 */
public interface StudentQaMapper
{
    List<StudentQaSession> selectSessions(@Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId, @Param("userId") Long userId);
    StudentQaSession selectSession(@Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId, @Param("userId") Long userId,
            @Param("sessionId") Long sessionId);
    int insertSession(StudentQaSession session);
    int updateSessionTitle(@Param("sessionId") Long sessionId, @Param("title") String title);
    int touchSession(Long sessionId);
    List<StudentQaMessage> selectMessages(@Param("tenantId") Long tenantId,
            @Param("sessionId") Long sessionId);
    int insertMessage(StudentQaMessage message);
    int completeAssistantMessage(StudentQaMessage message);
    int insertCitation(StudentQaCitation citation);
    List<StudentQaCitation> selectCitations(@Param("tenantId") Long tenantId,
            @Param("messageId") Long messageId);
    StudentQaCitation selectCitation(@Param("tenantId") Long tenantId,
            @Param("messageId") Long messageId, @Param("citationId") Long citationId);
}
