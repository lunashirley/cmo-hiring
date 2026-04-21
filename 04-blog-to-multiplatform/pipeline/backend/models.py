from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from database import Base


class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    url = Column(String, nullable=True)
    source_type = Column(String, default="url")  # url | paste
    raw_content = Column(Text, nullable=True)
    normalized_content = Column(Text, nullable=True)
    status = Column(String, default="ingesting")
    # ingesting | extracting | hitl | generating | done | error
    brand_voice_slug = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_msg = Column(Text, nullable=True)


class Atom(Base):
    __tablename__ = "atoms"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id"))
    type = Column(String)  # stat | insight | quote | anecdote
    text = Column(Text)
    edited_text = Column(Text, nullable=True)
    source_offset_start = Column(Integer, default=0)
    source_offset_end = Column(Integer, default=0)
    proposed_angle = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    origin = Column(String, default="extracted")  # extracted | manual
    priority = Column(Integer, default=0)
    approved = Column(Boolean, default=False)


class Output(Base):
    __tablename__ = "outputs"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id"))
    platform = Column(String)  # linkedin | x | newsletter | instagram
    version = Column(Integer, default=1)
    content = Column(Text)
    metadata_json = Column(Text, nullable=True)
    status = Column(String, default="draft")
    # draft | approved | escalated | edited | final
    agent_version = Column(Integer, default=1)
    template_version = Column(Integer, default=1)
    qa_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class OutputEdit(Base):
    __tablename__ = "output_edits"
    id = Column(String, primary_key=True)
    output_id = Column(String, ForeignKey("outputs.id"))
    diff = Column(Text)
    edited_content = Column(Text)
    edited_at = Column(DateTime, default=datetime.utcnow)


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(String, primary_key=True)
    output_id = Column(String, ForeignKey("outputs.id"))
    platform = Column(String)
    brand_voice_slug = Column(String)
    score = Column(Integer)  # 1-5
    tags_json = Column(Text, default="[]")
    note = Column(Text, nullable=True)
    rated_at = Column(DateTime, default=datetime.utcnow)


class QAResult(Base):
    __tablename__ = "qa_results"
    id = Column(String, primary_key=True)
    output_id = Column(String, ForeignKey("outputs.id"))
    attempt = Column(Integer)
    verdict = Column(String)  # pass | fail
    rubric_json = Column(Text)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BrandVoice(Base):
    __tablename__ = "brand_voices"
    slug = Column(String, primary_key=True)
    name = Column(String)
    version = Column(Integer, default=1)
    content_md = Column(Text)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AgentVersion(Base):
    __tablename__ = "agent_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent = Column(String)
    version = Column(Integer)
    content_md = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TemplateVersion(Base):
    __tablename__ = "template_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String)
    version = Column(Integer)
    content_md = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, default=datetime.utcnow)
    run_id = Column(String, nullable=True)
    agent = Column(String)
    event = Column(String)  # start | prompt | response | retry | pass | fail | error
    attempt = Column(Integer, default=1)
    duration_ms = Column(Integer, default=0)
    token_in = Column(Integer, default=0)
    token_out = Column(Integer, default=0)
    payload_ref = Column(String, nullable=True)
    notes = Column(Text, nullable=True)


class PayloadBlob(Base):
    __tablename__ = "payload_blobs"
    sha256 = Column(String, primary_key=True)
    content = Column(Text)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
