from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os
import shutil
from typing import Optional

from database import init_db
from models import *
from exam_service import ExamService

# 서비스 인스턴스
exam_service = ExamService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    await init_db()
    yield
    # 종료 시 (필요시 정리 작업)

app = FastAPI(title="AWS SAA 시험 연습 앱", version="1.0.0", lifespan=lifespan)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    exams = await exam_service.get_all_exams()
    return templates.TemplateResponse("index.html", {"request": request, "exams": exams})

# PDF 업로드
@app.post("/import/pdf")
async def import_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "PDF 파일만 업로드 가능합니다."}
        )
    
    try:
        # 임시 파일로 저장
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # PDF 파싱 및 시험 생성
        exam = await exam_service.create_exam_from_pdf(temp_path)
        
        # 임시 파일 삭제
        os.remove(temp_path)
        
        # 문제 수를 별도로 조회
        question_count = await exam_service.get_exam_question_count(exam.id)
        
        return JSONResponse(
            content={
                "success": True, 
                "message": f"'{exam.title}' 시험이 성공적으로 업로드되었습니다. (문제 수: {question_count}개)"
            }
        )
    except Exception as e:
        # 임시 파일 정리
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"PDF 파싱 중 오류가 발생했습니다: {str(e)}"}
        )

# 시험 상세 페이지
@app.get("/exam/{exam_id}", response_class=HTMLResponse)
async def exam_detail(request: Request, exam_id: int):
    exam = await exam_service.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="시험을 찾을 수 없습니다.")
    
    sections = await exam_service.get_exam_sections(exam_id)
    return templates.TemplateResponse("exam_detail.html", {
        "request": request, "exam": exam, "sections": sections
    })

# 새 세션 생성
@app.get("/session/new/{exam_id}")
async def new_session(exam_id: int, mode: str = "exam"):
    session = await exam_service.create_session(exam_id, mode)
    return RedirectResponse(url=f"/session/{session.id}")

# 세션 페이지
@app.get("/session/{session_id}", response_class=HTMLResponse)
async def session_page(request: Request, session_id: int):
    session = await exam_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    first_question = await exam_service.get_first_question(session_id)
    if not first_question:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    
    return templates.TemplateResponse("session.html", {
        "request": request, "session": session, "first_question": first_question
    })

# 문제 페이지
@app.get("/session/{session_id}/question/{question_id}", response_class=HTMLResponse)
async def question_page(request: Request, session_id: int, question_id: int):
    session = await exam_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    question = await exam_service.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    
    response = await exam_service.get_response(session_id, question_id)
    progress = await exam_service.get_session_progress(session_id)
    
    return templates.TemplateResponse("question.html", {
        "request": request,
        "session": session,
        "question": question,
        "response": response,
        "progress": progress
    })

# 응답 저장
@app.post("/session/{session_id}/response")
async def save_response(
    session_id: int,
    question_id: int = Form(...),
    choice_id: Optional[int] = Form(None),
    notes: str = Form(""),
    flagged: bool = Form(False)
):
    response = await exam_service.save_response(session_id, question_id, choice_id, notes, flagged)
    
    # 세션 정보 조회
    session = await exam_service.get_session(session_id)
    
    # 연습 모드인 경우 즉시 채점 결과만 반환 (정답/오답 여부만)
    if session.mode == "study":
        return {
            "success": True,
            "response_id": response.id,
            "is_correct": bool(response.is_correct)
        }
    
    return {"success": True, "response_id": response.id}

# 연습 모드에서 정답 확인
@app.get("/session/{session_id}/question/{question_id}/answer")
async def get_question_answer(session_id: int, question_id: int):
    result = await exam_service.get_question_result(session_id, question_id)
    return {
        "success": True,
        "is_correct": result["is_correct"],
        "correct_answer": result["correct_answer"],
        "explanation": result["explanation"]
    }

# 세션 제출
@app.post("/session/{session_id}/submit")
async def submit_session(session_id: int):
    session = await exam_service.submit_session(session_id)
    return RedirectResponse(url=f"/session/{session_id}/result")

# 결과 페이지
@app.get("/session/{session_id}/result", response_class=HTMLResponse)
async def result_page(request: Request, session_id: int):
    session = await exam_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    if not session.end_time:
        raise HTTPException(status_code=400, detail="아직 제출되지 않은 세션입니다.")
    
    return templates.TemplateResponse("result.html", {"request": request, "session": session})

# Admin 페이지
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    stats = await exam_service.get_admin_stats()
    exams = await exam_service.get_all_exams_with_counts()
    recent_sessions = await exam_service.get_recent_sessions()
    return templates.TemplateResponse("admin.html", {
        "request": request, "stats": stats, "exams": exams, "recent_sessions": recent_sessions
    })

# Admin PDF 업로드
@app.post("/admin/upload-pdf")
async def admin_upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "PDF 파일만 업로드 가능합니다."}
        )
    
    try:
        # 임시 파일로 저장
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # PDF 파싱 및 시험 생성
        exam = await exam_service.create_exam_from_pdf(temp_path)
        
        # 임시 파일 삭제
        os.remove(temp_path)
        
        # 문제 수를 별도로 조회
        question_count = await exam_service.get_exam_question_count(exam.id)
        
        return JSONResponse(
            content={
                "success": True, 
                "message": f"'{exam.title}' 시험이 성공적으로 업로드되었습니다. (문제 수: {question_count}개)"
            }
        )
    except Exception as e:
        # 임시 파일 정리
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"PDF 파싱 중 오류가 발생했습니다: {str(e)}"}
        )

# 시험 삭제
@app.delete("/admin/exam/{exam_id}/delete")
async def delete_exam(exam_id: int):
    success = await exam_service.delete_exam(exam_id)
    if success:
        return JSONResponse(content={"success": True, "message": "시험이 삭제되었습니다."})
    else:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "시험 삭제 중 오류가 발생했습니다."}
        )

# 시험 문제 관리
@app.get("/admin/exam/{exam_id}/questions", response_class=HTMLResponse)
async def admin_exam_questions(request: Request, exam_id: int):
    exam = await exam_service.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="시험을 찾을 수 없습니다.")
    
    questions_with_stats = await exam_service.get_exam_questions_with_responses(exam_id)
    return templates.TemplateResponse("admin_questions.html", {
        "request": request, "exam": exam, "questions": questions_with_stats
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
