package com.hezal.system.service;

import java.io.IOException;
import java.io.OutputStream;
import java.util.List;
import com.hezal.system.domain.StudentQaCitation;
import com.hezal.system.domain.StudentQaMessage;
import com.hezal.system.domain.StudentQaSession;
import com.hezal.system.domain.dto.QaObservationDetail;
import com.hezal.system.domain.dto.QaObservationItem;
import com.hezal.system.domain.dto.QaObservationQuery;
import com.hezal.system.domain.dto.QaObservationSummary;

/** 学员课程问答服务。 */
public interface IStudentQaService
{
    List<StudentQaSession> selectSessions(Long courseId, Long userId);

    StudentQaSession createSession(Long courseId, Long userId);

    void deleteSession(Long courseId, Long sessionId, Long userId);

    List<StudentQaMessage> selectMessages(Long courseId, Long sessionId, Long userId);

    StudentQaMessage ask(Long courseId, Long sessionId, Long userId, String question);
    void askStream(Long courseId, Long sessionId, Long userId, String question,
            OutputStream outputStream) throws IOException;

    StudentQaCitation selectCitation(Long courseId, Long sessionId, Long messageId,
            Long citationId, Long userId);

    QaObservationSummary selectObservationSummary(Long courseId, Long userId,
            QaObservationQuery query);

    List<QaObservationItem> selectObservationList(Long courseId, Long userId,
            QaObservationQuery query);

    QaObservationDetail selectObservationDetail(Long courseId, Long userId, Long messageId);
}
