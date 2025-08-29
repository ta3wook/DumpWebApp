from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    version = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    sections = relationship("Section", back_populates="exam", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    title = Column(String(255), nullable=False)
    order_index = Column(Integer, default=0)
    
    exam = relationship("Exam", back_populates="sections")
    questions = relationship("Question", back_populates="section", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    order_index = Column(Integer, default=0)
    images = Column(Text)  # JSON string of image paths
    
    section = relationship("Section", back_populates="questions")
    choices = relationship("Choice", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="question", cascade="all, delete-orphan")

class Choice(Base):
    __tablename__ = "choices"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    choice_text = Column(Text, nullable=False)
    choice_label = Column(String(10), nullable=False)  # A, B, C, D
    order_index = Column(Integer, default=0)
    
    question = relationship("Question", back_populates="choices")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    correct_choice_id = Column(Integer, ForeignKey("choices.id"), nullable=False)
    explanation = Column(Text)
    
    question = relationship("Question", back_populates="answers")
    correct_choice = relationship("Choice")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    mode = Column(String(20), default="exam")  # exam, study
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    score = Column(Float)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    
    exam = relationship("Exam")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_choice_id = Column(Integer, ForeignKey("choices.id"))
    is_correct = Column(Boolean)
    response_time = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    flagged = Column(Boolean, default=False)
    
    session = relationship("Session", back_populates="responses")
    question = relationship("Question", back_populates="responses")
    selected_choice = relationship("Choice")
