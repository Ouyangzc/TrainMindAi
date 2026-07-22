package com.hezal.system.service;

import java.util.List;
import java.io.InputStream;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.dto.StudentDocumentQuery;
import com.hezal.system.domain.vo.student.StudentCourseOutlineVO;
import com.hezal.system.domain.vo.student.StudentPublishedDocumentVO;

/** 学员端当前发布内容只读服务。 */
public interface IStudentPublishedContentService
{
    StudentCourseOutlineVO selectOutline(Long courseId, Long userId);

    List<StudentPublishedDocumentVO> selectDocuments(Long courseId, Long userId, StudentDocumentQuery query);

    StudentPublishedDocumentVO selectDocument(Long courseId, Long documentId, Long userId);

    CourseDocumentVersion selectPublishedVersion(Long courseId, Long documentId, Long userId);

    boolean isDownloadAllowed(Long courseId, Long userId);

    InputStream openPublishedVersionStream(CourseDocumentVersion version);
}
