package com.hezal.system.mapper;

import java.util.List;

import com.hezal.system.domain.CourseDocument;

/**
 * 课程资料数据访问接口。
 *
 * @author trainmind
 */
public interface CourseDocumentMapper
{
    int countCourseById(Long courseId);

    List<CourseDocument> selectCourseDocumentList(CourseDocument document);

    CourseDocument selectCourseDocumentById(Long id);

    CourseDocument lockCourseDocumentById(Long id);

    int insertCourseDocument(CourseDocument document);

    int updateCourseDocument(CourseDocument document);

    int deleteCourseDocumentById(Long id);
}
