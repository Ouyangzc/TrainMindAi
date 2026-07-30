package com.hezal.web.controller.course;

import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.common.core.page.TableDataInfo;
import com.hezal.system.domain.dto.QaObservationItem;
import com.hezal.system.domain.dto.QaObservationQuery;
import com.hezal.system.service.IStudentQaService;

/** 课程 AI 问答观测。 */
@RestController
@RequestMapping("/course/{courseId}/qa-observability")
public class CourseQaObservationController extends BaseController
{
    private final IStudentQaService studentQaService;

    public CourseQaObservationController(IStudentQaService studentQaService)
    {
        this.studentQaService = studentQaService;
    }

    @PreAuthorize("@ss.hasPermi('course:course:query')")
    @GetMapping("/summary")
    public AjaxResult summary(@PathVariable Long courseId, QaObservationQuery query)
    {
        return success(studentQaService.selectObservationSummary(courseId, getUserId(), query));
    }

    @PreAuthorize("@ss.hasPermi('course:course:query')")
    @GetMapping("/list")
    public TableDataInfo list(@PathVariable Long courseId, QaObservationQuery query)
    {
        startPage();
        List<QaObservationItem> list = studentQaService.selectObservationList(
                courseId, getUserId(), query);
        return getDataTable(list);
    }

    @PreAuthorize("@ss.hasPermi('course:course:query')")
    @GetMapping("/{messageId}")
    public AjaxResult detail(@PathVariable Long courseId, @PathVariable Long messageId)
    {
        return success(studentQaService.selectObservationDetail(courseId, getUserId(), messageId));
    }
}
