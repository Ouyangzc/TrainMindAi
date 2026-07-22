package com.hezal.system.service;

import java.util.List;
import com.hezal.system.domain.StudentQaCitation;
import com.hezal.system.domain.StudentQaMessage;
import com.hezal.system.domain.StudentQaSession;

/** 学员课程问答服务。 */
public interface IStudentQaService
{
    List<StudentQaSession> selectSessions(Long courseId, Long userId);

    StudentQaSession createSession(Long courseId, Long userId);

    List<StudentQaMessage> selectMessages(Long courseId, Long sessionId, Long userId);

    StudentQaMessage ask(Long courseId, Long sessionId, Long userId, String question);

    StudentQaCitation selectCitation(Long courseId, Long sessionId, Long messageId,
            Long citationId, Long userId);
}
