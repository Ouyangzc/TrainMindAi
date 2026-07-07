"""生成类：出题草稿、错题诊断、简答评分（返回草稿/建议，由 Java 落库）。"""

from fastapi import APIRouter

from app.services.generation import diagnose, generate_questions, grade_short_answer

router = APIRouter(tags=["generation"])


@router.post("/questions/generate")
async def generate(
    course_id: int,
    knowledge_point_id: int | None = None,
    count: int = 5,
) -> dict:
    """基于知识点检索 chunk -> LLM 出题 -> schema 校验 -> 返回 ai_draft。"""
    result = await generate_questions(course_id, knowledge_point_id, count)
    return {"questions": result}


@router.post("/diagnose")
async def diagnose_endpoint(wrong_answer_id: int) -> dict:
    """错题诊断（错因分类）。"""
    result = await diagnose(wrong_answer_id)
    return result


@router.post("/grade/short-answer")
async def grade(
    question: str,
    standard_answer: str,
    student_answer: str,
) -> dict:
    """简答题 AI 辅助评分。"""
    result = await grade_short_answer(question, standard_answer, student_answer)
    return result
