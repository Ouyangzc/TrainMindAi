package com.hezal.web.controller.student;

import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;
import com.hezal.common.core.controller.BaseController;
import com.hezal.common.core.domain.AjaxResult;
import com.hezal.system.domain.dto.StudentQaQuestionRequest;
import com.hezal.system.service.IStudentQaService;

/** 学员端课程 AI 问答。 */
@RestController
@RequestMapping("/student/courses/{courseId}/chat")
public class StudentQaController extends BaseController
{
    private final IStudentQaService studentQaService;

    public StudentQaController(IStudentQaService studentQaService)
    {
        this.studentQaService = studentQaService;
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/sessions")
    public AjaxResult sessions(@PathVariable Long courseId)
    {
        return success(studentQaService.selectSessions(courseId, getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @PostMapping("/sessions")
    public AjaxResult createSession(@PathVariable Long courseId)
    {
        return success(studentQaService.createSession(courseId, getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @DeleteMapping("/sessions/{sessionId}")
    public AjaxResult deleteSession(@PathVariable Long courseId, @PathVariable Long sessionId)
    {
        studentQaService.deleteSession(courseId, sessionId, getUserId());
        return success();
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/sessions/{sessionId}")
    public AjaxResult messages(@PathVariable Long courseId, @PathVariable Long sessionId)
    {
        return success(studentQaService.selectMessages(courseId, sessionId, getUserId()));
    }

    @PreAuthorize("isAuthenticated()")
    @PostMapping("/sessions/{sessionId}/messages")
    public AjaxResult ask(@PathVariable Long courseId, @PathVariable Long sessionId,
            @Valid @RequestBody StudentQaQuestionRequest request)
    {
        return success(studentQaService.ask(
                courseId, sessionId, getUserId(), request.getQuestion()));
    }

    @PreAuthorize("isAuthenticated()")
    @PostMapping(value = "/sessions/{sessionId}/messages/stream",
            produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public StreamingResponseBody askStream(@PathVariable Long courseId, @PathVariable Long sessionId,
            @Valid @RequestBody StudentQaQuestionRequest request)
    {
        Long userId = getUserId();
        return outputStream -> studentQaService.askStream(
                courseId, sessionId, userId, request.getQuestion(), outputStream);
    }

    @PreAuthorize("isAuthenticated()")
    @GetMapping("/sessions/{sessionId}/messages/{messageId}/citations/{citationId}")
    public AjaxResult citation(@PathVariable Long courseId, @PathVariable Long sessionId,
            @PathVariable Long messageId, @PathVariable Long citationId)
    {
        return success(studentQaService.selectCitation(
                courseId, sessionId, messageId, citationId, getUserId()));
    }
}
