package com.hezal.system.domain.vo.student;

import java.util.ArrayList;
import java.util.List;

/** 学员端当前发布版课程目录。 */
public class StudentCourseOutlineVO
{
    private Long courseId;
    private Long knowledgeBaseVersionId;
    private Integer versionNo;
    private List<StudentCourseModuleVO> modules = new ArrayList<>();

    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getKnowledgeBaseVersionId() { return knowledgeBaseVersionId; }
    public void setKnowledgeBaseVersionId(Long knowledgeBaseVersionId) { this.knowledgeBaseVersionId = knowledgeBaseVersionId; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public List<StudentCourseModuleVO> getModules() { return modules; }
    public void setModules(List<StudentCourseModuleVO> modules) { this.modules = modules; }
}
