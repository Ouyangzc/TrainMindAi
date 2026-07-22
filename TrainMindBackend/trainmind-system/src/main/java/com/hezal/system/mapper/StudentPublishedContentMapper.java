package com.hezal.system.mapper;

import java.util.List;
import org.apache.ibatis.annotations.Param;
import com.hezal.system.domain.dto.StudentDocumentQuery;
import com.hezal.system.domain.vo.student.StudentPublishedDocumentVO;

/** 学员端当前发布内容只读查询。 */
public interface StudentPublishedContentMapper
{
    List<StudentPublishedDocumentVO> selectPublishedDocuments(
            @Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId,
            @Param("versionId") Long versionId,
            @Param("query") StudentDocumentQuery query);

    StudentPublishedDocumentVO selectPublishedDocument(
            @Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId,
            @Param("versionId") Long versionId,
            @Param("documentId") Long documentId);

    String selectPublishedModuleName(
            @Param("tenantId") Long tenantId,
            @Param("courseId") Long courseId,
            @Param("versionId") Long versionId,
            @Param("moduleId") Long moduleId);
}
