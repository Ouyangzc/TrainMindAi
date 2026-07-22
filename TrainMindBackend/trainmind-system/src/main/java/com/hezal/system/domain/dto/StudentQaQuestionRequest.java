package com.hezal.system.domain.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** 学员提问请求。 */
public class StudentQaQuestionRequest
{
    @NotBlank(message = "问题不能为空")
    @Size(max = 2000, message = "问题长度不能超过2000个字符")
    private String question;

    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }
}
