package com.hezal.system.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.hezal.common.core.domain.BaseEntity;

/**
 * 课程模块 course_module
 *
 * @author trainmind
 */
public class CourseModule extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long tenantId;

    private Long courseId;

    private String moduleCode;

    private String moduleName;

    private String description;

    private Integer sortOrder;

    private String status;

    private String delFlag;

    public Long getId()
    {
        return id;
    }

    public void setId(Long id)
    {
        this.id = id;
    }

    public Long getTenantId()
    {
        return tenantId;
    }

    public void setTenantId(Long tenantId)
    {
        this.tenantId = tenantId;
    }

    @NotNull(message = "课程ID不能为空")
    public Long getCourseId()
    {
        return courseId;
    }

    public void setCourseId(Long courseId)
    {
        this.courseId = courseId;
    }

    @Size(max = 64, message = "模块编码长度不能超过64个字符")
    public String getModuleCode()
    {
        return moduleCode;
    }

    public void setModuleCode(String moduleCode)
    {
        this.moduleCode = moduleCode;
    }

    @NotBlank(message = "模块名称不能为空")
    @Size(max = 200, message = "模块名称长度不能超过200个字符")
    public String getModuleName()
    {
        return moduleName;
    }

    public void setModuleName(String moduleName)
    {
        this.moduleName = moduleName;
    }

    @Size(max = 1000, message = "模块说明长度不能超过1000个字符")
    public String getDescription()
    {
        return description;
    }

    public void setDescription(String description)
    {
        this.description = description;
    }

    public Integer getSortOrder()
    {
        return sortOrder;
    }

    public void setSortOrder(Integer sortOrder)
    {
        this.sortOrder = sortOrder;
    }

    public String getStatus()
    {
        return status;
    }

    public void setStatus(String status)
    {
        this.status = status;
    }

    public String getDelFlag()
    {
        return delFlag;
    }

    public void setDelFlag(String delFlag)
    {
        this.delFlag = delFlag;
    }

    @Override
    public String toString()
    {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("id", getId())
                .append("tenantId", getTenantId())
                .append("courseId", getCourseId())
                .append("moduleCode", getModuleCode())
                .append("moduleName", getModuleName())
                .append("description", getDescription())
                .append("sortOrder", getSortOrder())
                .append("status", getStatus())
                .append("delFlag", getDelFlag())
                .append("createBy", getCreateBy())
                .append("createTime", getCreateTime())
                .append("updateBy", getUpdateBy())
                .append("updateTime", getUpdateTime())
                .append("remark", getRemark())
                .toString();
    }
}
