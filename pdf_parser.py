import fitz  # PyMuPDF
import re
import json
from typing import List, Dict, Any
from models import Exam, Section, Question, Choice, Answer

class PDFParser:
    def __init__(self):
        self.question_pattern = r'QUESTION NO:\s*(\d+)'
        self.choice_pattern = r'^([A-D])\.\s*(.+)$'
        self.answer_pattern = r'Answer:\s*([A-D])'
        self.explanation_pattern = r'Explanation:\s*(.+)'
        
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 파일을 파싱하여 시험 데이터를 추출"""
        try:
            doc = fitz.open(pdf_path)
            text_content = ""
            
            # 모든 페이지의 텍스트 추출
            for page in doc:
                text_content += page.get_text()
            
            doc.close()
            
            # 시험 정보 추출
            exam_info = self._extract_exam_info(text_content)
            
            # 문제들 파싱
            questions = self._parse_questions(text_content)
            
            print(f"파싱 완료: {len(questions)}개 문제 발견")
            
            return {
                "exam_info": exam_info,
                "questions": questions
            }
        except Exception as e:
            print(f"PDF 파싱 중 오류: {e}")
            raise
    
    def _extract_exam_info(self, text: str) -> Dict[str, str]:
        """시험 정보 추출"""
        lines = text.split('\n')
        title = "AWS SAA 시험"
        version = "Unknown"
        
        # 첫 번째 줄에서 제목 추출 시도
        for line in lines[:10]:
            if "AWS" in line and ("SAA" in line or "Solutions" in line):
                title = line.strip()
                break
        
        # 버전 정보 추출
        version_match = re.search(r'V(\d+\.\d+)', text)
        if version_match:
            version = f"V{version_match.group(1)}"
        
        return {
            "title": title,
            "version": version,
            "description": f"AWS SAA 시험 문제집 - {version}"
        }
    
    def _parse_questions(self, text: str) -> List[Dict[str, Any]]:
        """문제들을 파싱"""
        questions = []
        
        # 문제 번호로 분할 (더 유연한 패턴)
        question_blocks = re.split(r'QUESTION NO:\s*\d+', text, flags=re.IGNORECASE)[1:]
        
        for i, block in enumerate(question_blocks, 1):
            try:
                question_data = self._create_question_dict(i, block)
                if question_data:
                    questions.append(question_data)
            except Exception as e:
                print(f"문제 {i} 파싱 중 오류: {e}")
                continue
        
        return questions
    
    def _create_question_dict(self, question_number: int, block: str) -> Dict[str, Any]:
        """개별 문제 데이터 생성"""
        lines = block.strip().split('\n')
        
        # 문제 텍스트 추출
        question_text = ""
        choices = []
        answer = None
        explanation = ""
        
        in_question = True
        in_choices = False
        in_answer = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 답안 섹션 시작 (대소문자 구분 없이)
            if re.match(r'^Answer:', line, re.IGNORECASE):
                in_question = False
                in_choices = False
                in_answer = True
                answer_match = re.search(self.answer_pattern, line, re.IGNORECASE)
                if answer_match:
                    answer = answer_match.group(1).upper()  # 대문자로 정규화
                continue
            
            # 설명 섹션 시작 (대소문자 구분 없이)
            if re.match(r'^Explanation:', line, re.IGNORECASE):
                in_answer = False
                explanation_match = re.search(self.explanation_pattern, line, re.IGNORECASE)
                if explanation_match:
                    explanation = explanation_match.group(1)
                continue
            
            # 선택지 확인 (더 유연한 패턴)
            choice_match = re.search(r'^([A-D])[\.\s]+(.+)$', line, re.IGNORECASE)
            if choice_match:
                in_question = False
                in_choices = True
                choice_label = choice_match.group(1).upper()  # 대문자로 정규화
                choice_text = choice_match.group(2).strip()
                
                # 선택지 텍스트가 다음 줄에 이어지는지 확인
                next_line_idx = lines.index(line) + 1
                while next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if not next_line:
                        break
                    # 다음 줄이 새로운 선택지나 답안/설명 섹션인지 확인
                    if (re.match(r'^[A-D][\.\s]', next_line, re.IGNORECASE) or 
                        re.match(r'^Answer:', next_line, re.IGNORECASE) or
                        re.match(r'^Explanation:', next_line, re.IGNORECASE)):
                        break
                    # 선택지 텍스트에 추가
                    choice_text += " " + next_line
                    next_line_idx += 1
                
                choices.append({
                    "label": choice_label,
                    "text": choice_text,
                    "order_index": len(choices)
                })
                continue
            
            # 문제 텍스트 또는 설명 추가
            if in_question:
                question_text += line + "\n"
            elif in_answer and line and not re.match(r'^Answer:', line, re.IGNORECASE):
                explanation += line + "\n"
        
        # 최소한 문제 텍스트와 선택지가 있어야 함
        if not question_text.strip() or len(choices) < 2:
            print(f"문제 {question_number}: 텍스트 또는 선택지 부족 - 텍스트: {len(question_text.strip())}, 선택지: {len(choices)}")
            return None
        
        return {
            "question_number": question_number,
            "question_text": question_text.strip(),
            "choices": choices,
            "answer": answer,
            "explanation": explanation.strip(),
            "images": []  # 이미지 추출은 향후 구현
        }
    
    def _extract_version(self, text: str) -> str:
        """PDF에서 버전 정보 추출"""
        version_patterns = [
            r'V(\d+\.\d+)',
            r'Version\s*(\d+\.\d+)',
            r'v(\d+\.\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, text)
            if match:
                return f"V{match.group(1)}"
        
        return "Unknown"
    
    def _extract_images(self, page) -> List[str]:
        """페이지에서 이미지 추출 (향후 구현)"""
        # 이미지 추출 로직은 향후 구현
        return []
