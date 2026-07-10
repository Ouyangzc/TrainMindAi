package com.hezal.system.service;

import java.io.InputStream;
import java.util.List;

import org.springframework.web.multipart.MultipartFile;

import com.hezal.system.domain.CourseDocument;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.DocumentParseTask;

/**
 * 课程资料业务接口。
 *
 * @author trainmind
 */
public interface ICourseDocumentService
{
    List<CourseDocument> selectCourseDocumentList(CourseDocument document);

    CourseDocumentVersion uploadDocument(Long courseId, Long moduleId, String title,
            String remark, MultipartFile file, String username);

    CourseDocumentVersion uploadVersion(Long courseId, Long documentId,
            String remark, MultipartFile file, String username);

    List<CourseDocumentVersion> selectVersions(Long courseId, Long documentId);

    CourseDocumentVersion selectVersion(Long courseId, Long documentId, Long versionId);

    InputStream openVersionStream(CourseDocumentVersion version);

    DocumentParseTask triggerParse(Long courseId, Long documentId, Long versionId, String username);

    DocumentParseTask selectParseTask(Long courseId, Long documentId, Long versionId, String username);

    int deleteCourseDocument(Long courseId, Long documentId);
}
