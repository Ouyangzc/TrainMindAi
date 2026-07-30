package com.hezal.system.domain.dto;

/** AI问答多轮上下文单轮历史。 */
public class AiQaHistoryTurn
{
    private String user;
    private String assistant;

    public AiQaHistoryTurn()
    {
    }

    public AiQaHistoryTurn(String user, String assistant)
    {
        this.user = user;
        this.assistant = assistant;
    }

    public String getUser() { return user; }
    public void setUser(String user) { this.user = user; }
    public String getAssistant() { return assistant; }
    public void setAssistant(String assistant) { this.assistant = assistant; }
}
