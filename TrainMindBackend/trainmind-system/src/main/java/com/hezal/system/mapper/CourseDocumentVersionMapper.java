package com.hezal.system.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Param;

import com.hezal.system.domain.CourseDocumentVersion;

/**
 * 课程资料版本数据访问接口。
 *
 * @author trainmind
 */
public interface CourseDocumentVersionMapper
{
    List<CourseDocumentVersion> selectVersionsByDocumentId(Long documentId);

    CourseDocumentVersion selectVersion(@Param("courseId") Long courseId,
            @Param("documentId") Long documentId, @Param("versionId") Long versionId);

    CourseDocumentVersion lockVersion(@Param("courseId") Long courseId,
            @Param("documentId") Long documentId, @Param("versionId") Long versionId);

    Integer selectMaxVersionNo(Long documentId);

    int insertCourseDocumentVersion(CourseDocumentVersion version);

    int updateCourseDocumentVersion(CourseDocumentVersion version);

    int deleteVersionsByDocumentId(Long documentId);
}
