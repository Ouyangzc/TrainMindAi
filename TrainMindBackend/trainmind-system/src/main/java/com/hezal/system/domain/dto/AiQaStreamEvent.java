package com.hezal.system.domain.dto;

import com.fasterxml.jackson.databind.JsonNode;

/** AI问答流式事件。 */
public class AiQaStreamEvent
{
    private String event;
    private JsonNode data;

    public AiQaStreamEvent()
    {
    }

    public AiQaStreamEvent(String event, JsonNode data)
    {
        this.event = event;
        this.data = data;
    }

    public String getEvent() { return event; }
    public void setEvent(String event) { this.event = event; }
    public JsonNode getData() { return data; }
    public void setData(JsonNode data) { this.data = data; }
}
