from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, case
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from database import AsyncSessionLocal
from models import Exam, Section, Question, Choice, Answer, Session, Response
from pdf_parser import PDFParser

class ExamService:
    def __init__(self):
        self.pdf_parser = PDFParser()
    
    async def get_all_exams(self) -> List[Exam]:
        """모든 시험 목록 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Exam).order_by(Exam.created_at.desc())
            )
            return result.scalars().all()
    
    async def get_exam(self, exam_id: int) -> Optional[Exam]:
        """특정 시험 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Exam).where(Exam.id == exam_id)
            )
            return result.scalar_one_or_none()
    
    async def get_exam_sections(self, exam_id: int) -> List[Section]:
        """시험의 섹션 목록 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Section)
                .where(Section.exam_id == exam_id)
                .order_by(Section.order_index)
            )
            return result.scalars().all()
    
    async def create_exam_from_pdf(self, pdf_path: str) -> Exam:
        """PDF에서 시험 데이터 생성"""
        # PDF 파싱
        parsed_data = self.pdf_parser.parse_pdf(pdf_path)
        
        async with AsyncSessionLocal() as session:
            # 시험 생성
            exam = Exam(
                title=parsed_data["exam_info"]["title"],
                version=parsed_data["exam_info"]["version"],
                description=parsed_data["exam_info"]["description"]
            )
            session.add(exam)
            await session.flush()
            
            # 기본 섹션 생성
            section = Section(
                exam_id=exam.id,
                title="기본 섹션",
                order_index=0
            )
            session.add(section)
            await session.flush()
            
            # 문제들 생성
            for i, question_data in enumerate(parsed_data["questions"]):
                question = Question(
                    section_id=section.id,
                    question_text=question_data["question_text"],
                    order_index=i,
                    images=json.dumps(question_data["images"])
                )
                session.add(question)
                await session.flush()
                
                # 선택지들 생성
                choices = []
                for choice_data in question_data["choices"]:
                    choice = Choice(
                        question_id=question.id,
                        choice_text=choice_data["text"],
                        choice_label=choice_data["label"],
                        order_index=choice_data["order_index"]
                    )
                    session.add(choice)
                    await session.flush()  # ID 생성을 위해 flush
                    choices.append(choice)
                
                # 답안 생성
                if question_data["answer"]:
                    # 정답 선택지 찾기
                    correct_choice = None
                    for choice in choices:
                        if choice.choice_label == question_data["answer"]:
                            correct_choice = choice
                            break
                    
                    if correct_choice:
                        answer = Answer(
                            question_id=question.id,
                            correct_choice_id=correct_choice.id,
                            explanation=question_data["explanation"]
                        )
                        session.add(answer)
            
            await session.commit()
            
            # Exam 객체를 다시 조회하여 반환 (세션에 바인딩된 객체)
            result = await session.execute(
                select(Exam).options(selectinload(Exam.sections)).where(Exam.id == exam.id)
            )
            return result.scalar_one()
    
    async def create_session(self, exam_id: int, mode: str = "exam") -> Session:
        """새로운 시험 세션 생성"""
        async with AsyncSessionLocal() as session:
            # 총 문제 수 계산
            result = await session.execute(
                select(func.count(Question.id))
                .join(Section, Question.section_id == Section.id)
                .where(Section.exam_id == exam_id)
            )
            total_questions = result.scalar()
            
            # 세션 생성
            exam_session = Session(
                exam_id=exam_id,
                mode=mode,
                total_questions=total_questions
            )
            session.add(exam_session)
            await session.commit()
            await session.refresh(exam_session)
            
            return exam_session
    
    async def get_session(self, session_id: int) -> Optional[Session]:
        """세션 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Session).options(selectinload(Session.exam)).where(Session.id == session_id)
            )
            return result.scalar_one_or_none()
    
    async def get_first_question(self, session_id: int) -> Optional[Question]:
        """세션의 첫 번째 문제 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .join(Session, Exam.id == Session.exam_id)
                .where(Session.id == session_id)
                .order_by(Question.order_index)
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_question(self, question_id: int) -> Optional[Question]:
        """특정 문제 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Question)
                .options(selectinload(Question.choices))
                .where(Question.id == question_id)
            )
            return result.scalar_one_or_none()
    
    async def get_response(self, session_id: int, question_id: int) -> Optional[Response]:
        """특정 문제의 응답 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Response)
                .where(Response.session_id == session_id, Response.question_id == question_id)
            )
            return result.scalar_one_or_none()
    
    async def save_response(self, session_id: int, question_id: int, choice_id: Optional[int], notes: str = "", flagged: bool = False) -> Response:
        """응답 저장"""
        async with AsyncSessionLocal() as db:
            # 기존 응답 확인
            existing_response = await self.get_response(session_id, question_id)
            
            def is_choice_correct(choice_id, answer):
                try:
                    if not choice_id or str(choice_id).strip() == "":
                        print(f"[DEBUG] choice_id is None or empty: {choice_id}")
                        return False
                    cid = int(choice_id)
                    acid = int(answer.correct_choice_id)
                    print(f"[DEBUG] 비교: 선택={cid}, 정답={acid}")
                    return cid == acid
                except Exception as e:
                    print(f"[DEBUG] 비교 오류: {e}, choice_id={choice_id}, answer.correct_choice_id={getattr(answer, 'correct_choice_id', None)}")
                    return False
            
            if existing_response:
                # 기존 응답 업데이트
                existing_response.selected_choice_id = choice_id
                existing_response.notes = notes
                existing_response.flagged = flagged
                existing_response.response_time = datetime.now()
                
                # 정답 여부 확인
                if choice_id:
                    result = await db.execute(
                        select(Answer).where(Answer.question_id == question_id)
                    )
                    answer = result.scalar_one_or_none()
                    if answer:
                        existing_response.is_correct = is_choice_correct(choice_id, answer)
                
                await db.commit()
                return existing_response
            else:
                # 새 응답 생성
                is_correct = None
                if choice_id:
                    result = await db.execute(
                        select(Answer).where(Answer.question_id == question_id)
                    )
                    answer = result.scalar_one_or_none()
                    if answer:
                        is_correct = is_choice_correct(choice_id, answer)
                
                response = Response(
                    session_id=session_id,
                    question_id=question_id,
                    selected_choice_id=choice_id,
                    is_correct=is_correct,
                    notes=notes,
                    flagged=flagged
                )
                db.add(response)
                await db.commit()
                await db.refresh(response)
                return response
    
    async def submit_session(self, session_id: int) -> Session:
        """세션 제출 및 점수 계산"""
        async with AsyncSessionLocal() as session:
            # 세션 조회
            result = await session.execute(
                select(Session).where(Session.id == session_id)
            )
            exam_session = result.scalar_one_or_none()
            
            if not exam_session:
                raise ValueError("Session not found")
            
            # 정답 수 계산
            result = await session.execute(
                select(func.count(Response.id))
                .where(Response.session_id == session_id, Response.is_correct == True)
            )
            correct_answers = result.scalar()
            
            # 점수 계산
            score = (correct_answers / exam_session.total_questions * 100) if exam_session.total_questions > 0 else 0
            
            # 세션 업데이트
            exam_session.end_time = datetime.now()
            exam_session.score = score
            exam_session.correct_answers = correct_answers
            
            await session.commit()
            await session.refresh(exam_session)
            
            return exam_session
    
    async def get_session_questions(self, session_id: int) -> List[Question]:
        """세션의 모든 문제 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .join(Session, Exam.id == Session.exam_id)
                .where(Session.id == session_id)
                .order_by(Question.order_index)
            )
            return result.scalars().all()
    
    async def get_next_question(self, session_id: int, current_question_id: int) -> Optional[Question]:
        """다음 문제 조회"""
        async with AsyncSessionLocal() as session:
            # 현재 문제의 순서 찾기
            result = await session.execute(
                select(Question.order_index)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .join(Session, Exam.id == Session.exam_id)
                .where(Session.id == session_id, Question.id == current_question_id)
            )
            current_order = result.scalar_one_or_none()
            
            if current_order is None:
                return None
            
            # 다음 문제 조회
            result = await session.execute(
                select(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .join(Session, Exam.id == Session.exam_id)
                .where(Session.id == session_id, Question.order_index > current_order)
                .order_by(Question.order_index)
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_previous_question(self, session_id: int, current_question_id: int) -> Optional[Question]:
        """이전 문제 조회"""
        async with AsyncSessionLocal() as session:
            # 현재 문제의 순서 찾기
            result = await session.execute(
                select(Question.order_index)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .join(Session, Exam.id == Session.exam_id)
                .where(Session.id == session_id, Question.id == current_question_id)
            )
            current_order = result.scalar_one_or_none()
            
            if current_order is None:
                return None
            
            # 이전 문제 조회
            result = await session.execute(
                select(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .join(Session, Exam.id == Session.exam_id)
                .where(Session.id == session_id, Question.order_index < current_order)
                .order_by(Question.order_index.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_session_progress(self, session_id: int) -> Dict[str, Any]:
        """세션 진행 상황 조회"""
        async with AsyncSessionLocal() as session:
            # 총 응답 수
            result = await session.execute(
                select(func.count(Response.id))
                .where(Response.session_id == session_id)
            )
            answered_count = result.scalar()
            
            # 정답 수
            result = await session.execute(
                select(func.count(Response.id))
                .where(Response.session_id == session_id, Response.is_correct == True)
            )
            correct_count = result.scalar()
            
            # 세션 정보
            result = await session.execute(
                select(Session).where(Session.id == session_id)
            )
            exam_session = result.scalar_one_or_none()
            
            if not exam_session:
                return {}
            
            return {
                "total_questions": exam_session.total_questions,
                "answered_count": answered_count,
                "correct_count": correct_count,
                "progress_percentage": (answered_count / exam_session.total_questions * 100) if exam_session.total_questions > 0 else 0
            }
    
    async def get_question_result(self, session_id: int, question_id: int) -> Dict[str, Any]:
        """문제 결과 조회 (연습 모드용)"""
        async with AsyncSessionLocal() as session:
            # 응답 조회
            result = await session.execute(
                select(Response)
                .where(Response.session_id == session_id, Response.question_id == question_id)
            )
            response = result.scalar_one_or_none()
            
            if not response:
                return {
                    "is_correct": None,
                    "correct_answer": None,
                    "explanation": None
                }
            
            # 정답 정보 조회
            result = await session.execute(
                select(Answer, Choice.choice_label)
                .join(Choice, Answer.correct_choice_id == Choice.id)
                .where(Answer.question_id == question_id)
            )
            answer_info = result.first()
            
            if not answer_info:
                return {
                    "is_correct": None,
                    "correct_answer": None,
                    "explanation": None
                }
            
            answer, correct_choice_label = answer_info
            
            return {
                "is_correct": response.is_correct,
                "correct_answer": correct_choice_label,
                "explanation": answer.explanation
            }
    
    # Admin 기능들
    async def get_admin_stats(self) -> Dict[str, Any]:
        """관리자 통계 조회"""
        async with AsyncSessionLocal() as session:
            # 총 시험 수
            result = await session.execute(select(func.count(Exam.id)))
            total_exams = result.scalar()
            
            # 총 문제 수
            result = await session.execute(select(func.count(Question.id)))
            total_questions = result.scalar()
            
            # 총 세션 수
            result = await session.execute(select(func.count(Session.id)))
            total_sessions = result.scalar()
            
            # 평균 점수
            result = await session.execute(
                select(func.avg(Session.score))
                .where(Session.score.isnot(None))
            )
            avg_score = result.scalar() or 0
            
            return {
                "total_exams": total_exams,
                "total_questions": total_questions,
                "total_sessions": total_sessions,
                "avg_score": round(avg_score, 2)
            }
    
    async def get_all_exams_with_counts(self) -> List[Dict[str, Any]]:
        """모든 시험과 문제 수 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Exam,
                    func.count(Question.id).label('question_count')
                )
                .select_from(Exam)
                .outerjoin(Section, Exam.id == Section.exam_id)
                .outerjoin(Question, Section.id == Question.section_id)
                .group_by(Exam.id)
                .order_by(Exam.created_at.desc())
            )
            return [{"exam": row[0], "question_count": row[1]} for row in result.all()]
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Session]:
        """최근 세션 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Session)
                .options(selectinload(Session.exam))
                .order_by(Session.start_time.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def delete_exam(self, exam_id: int) -> bool:
        """시험 삭제"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    delete(Exam).where(Exam.id == exam_id)
                )
                await session.commit()
                return result.rowcount > 0
            except Exception:
                await session.rollback()
                return False
    
    async def get_exam_question_count(self, exam_id: int) -> int:
        """시험의 문제 수 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(Question.id))
                .select_from(Question)
                .join(Section, Question.section_id == Section.id)
                .where(Section.exam_id == exam_id)
            )
            return result.scalar()
    
    async def get_exam_questions_with_responses(self, exam_id: int) -> List[Dict[str, Any]]:
        """시험의 문제들과 응답 통계 조회"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Question,
                    func.count(Response.id).label('response_count'),
                    func.count(case((Response.is_correct == True, 1))).label('correct_count')
                )
                .select_from(Question)
                .join(Section, Question.section_id == Section.id)
                .outerjoin(Response, Question.id == Response.question_id)
                .where(Section.exam_id == exam_id)
                .group_by(Question.id)
                .order_by(Question.order_index)
            )
            return [
                {
                    "question": row[0],
                    "response_count": row[1],
                    "correct_count": row[2],
                    "accuracy": round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2)
                }
                for row in result.all()
            ]
