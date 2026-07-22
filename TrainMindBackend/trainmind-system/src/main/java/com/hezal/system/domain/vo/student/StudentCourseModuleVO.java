package com.hezal.system.domain.vo.student;

import java.util.ArrayList;
import java.util.List;

/** 学员端课程目录模块。 */
public class StudentCourseModuleVO
{
    private Long moduleId;
    private String moduleCode;
    private String moduleName;
    private String description;
    private Integer sortOrder;
    private List<StudentPublishedDocumentVO> documents = new ArrayList<>();

    public Long getModuleId() { return moduleId; }
    public void setModuleId(Long moduleId) { this.moduleId = moduleId; }
    public String getModuleCode() { return moduleCode; }
    public void setModuleCode(String moduleCode) { this.moduleCode = moduleCode; }
    public String getModuleName() { return moduleName; }
    public void setModuleName(String moduleName) { this.moduleName = moduleName; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public Integer getSortOrder() { return sortOrder; }
    public void setSortOrder(Integer sortOrder) { this.sortOrder = sortOrder; }
    public List<StudentPublishedDocumentVO> getDocuments() { return documents; }
    public void setDocuments(List<StudentPublishedDocumentVO> documents) { this.documents = documents; }
}
