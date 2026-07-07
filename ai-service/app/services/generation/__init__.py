"""生成：出题 / 错题诊断 / 简答评分。

脚手架阶段：给出函数签名与草稿实现。
"""

from app.gateway.llm_client import LlmClient


async def generate_questions(
    course_id: int,
    knowledge_point_id: int | None,
    count: int = 5,
    question_types: list[str] | None = None,
) -> list[dict]:
    """基于 chunk 检索结果产出题目草稿。脚手架阶段返回占位。"""
    raise NotImplementedError("AI 出题待实现")


async def diagnose(wrong_answer_id: int) -> dict:
    """错题诊断。脚手架阶段返回占位。"""
    raise NotImplementedError("错题诊断待实现")


async def grade_short_answer(question: str, standard: str, student: str) -> dict:
    """简答题 AI 辅助评分。脚手架阶段返回占位。"""
    llm = LlmClient()
    prompt = [
        {
            "role": "system",
            "content": "你是一个评分助手。请根据标准答案，为学生的简答回答打分（满分 100），"
            "并给出简短理由。仅返回 JSON：{\"score\": int, \"reason\": str}",
        },
        {
            "role": "user",
            "content": f"标准答案：{standard}\n\n学生回答：{student}\n\n题目：{question}",
        },
    ]
    result = await llm.chat(prompt, temperature=0.3)
    return {"result": result, "model": llm.model}
