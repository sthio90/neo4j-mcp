"""Data types and models for the Neo4j EHR MCP Server."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_serializer


# Base class for all models with JSON serialization support
class BaseNodeModel(BaseModel):
    """Base model with datetime serialization support."""
    
    @field_serializer('*', mode='wrap')
    def serialize_datetime(self, value, serializer):
        """Serialize datetime fields to ISO format."""
        if isinstance(value, datetime):
            return value.isoformat() if value else None
        return serializer(value)


# Node Models
class Patient(BaseNodeModel):
    """Patient node model."""
    subject_id: str
    gender: Optional[str] = None
    anchor_age: Optional[int] = None
    anchor_year: Optional[int] = None
    anchor_year_group: Optional[str] = None
    dod: Optional[datetime] = None


class Admission(BaseNodeModel):
    """Admission node model."""
    hadm_id: str
    admission_type: Optional[str] = None
    admittime: Optional[datetime] = None
    dischtime: Optional[datetime] = None
    deathtime: Optional[datetime] = None
    admission_location: Optional[str] = None
    discharge_location: Optional[str] = None
    insurance: Optional[str] = None
    language: Optional[str] = None
    marital_status: Optional[str] = None
    race: Optional[str] = None
    edregtime: Optional[datetime] = None
    edouttime: Optional[datetime] = None
    hospital_expire_flag: Optional[int] = None
    admit_provider_id: Optional[str] = None


class DischargeNote(BaseNodeModel):
    """Discharge note node model."""
    note_id: str
    hadm_id: Optional[str] = None
    subject_id: Optional[str] = None
    note_type: str
    text: str
    note_seq: Optional[int] = None
    charttime: Optional[datetime] = None
    storetime: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    embedding_created: Optional[datetime] = None


class RadiologyReport(BaseNodeModel):
    """Radiology report node model."""
    note_id: str
    hadm_id: Optional[str] = None
    subject_id: Optional[str] = None
    note_type: str
    text: str
    note_seq: Optional[int] = None
    charttime: Optional[datetime] = None
    storetime: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    embedding_created: Optional[datetime] = None


class LabEvent(BaseNodeModel):
    """Lab event node model."""
    lab_event_id: str
    subject_id: str
    hadm_id: Optional[str] = None
    charttime: datetime
    label: str
    itemid: Optional[str] = None
    category: Optional[str] = None
    flag: Optional[str] = None
    value: Optional[str] = None
    comments: Optional[str] = None
    ref_range_upper: Optional[float] = None
    ref_range_lower: Optional[float] = None
    fluid: Optional[str] = None
    priority: Optional[str] = None
    storetime: Optional[datetime] = None


class Medication(BaseNodeModel):
    """Medication node model."""
    medication: str
    route: Optional[str] = None
    hadm_id: Optional[str] = None
    subject_id: Optional[str] = None
    frequency: Optional[str] = None
    verifiedtime: Optional[datetime] = None


class Diagnosis(BaseNodeModel):
    """Diagnosis node model."""
    icd_code: str
    long_title: Optional[str] = None
    synonyms: Optional[List[str]] = None
    hadm_id: Optional[str] = None
    subject_id: Optional[str] = None
    seq_num: Optional[int] = None
    icd_version: Optional[int] = None


class Procedure(BaseNodeModel):
    """Procedure node model."""
    icd_code: str
    long_title: Optional[str] = None
    hadm_id: Optional[str] = None
    seq_num: Optional[int] = None
    chartdate: Optional[datetime] = None
    icd_version: Optional[int] = None


# Response Models
class PatientResponse(BaseNodeModel):
    """Response model for patient queries."""
    patient: Patient
    admissions: Optional[List[Admission]] = None
    diagnoses: Optional[List[Diagnosis]] = None
    procedures: Optional[List[Procedure]] = None
    medications: Optional[List[Medication]] = None
    lab_events: Optional[List[LabEvent]] = None


class NoteSearchResult(BaseNodeModel):
    """Result model for note searches."""
    note_id: str
    note_type: str
    subject_id: Optional[str] = None
    hadm_id: Optional[str] = None
    charttime: Optional[datetime] = None
    text: str
    score: Optional[float] = None  # For semantic search


class SchemaInfo(BaseNodeModel):
    """Schema information model."""
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]


# Request parameter types
OutputFormat = Literal["json", "table", "text", "markdown"]
NoteType = Literal["discharge", "radiology", "all"]


# Tool response model
class ToolResponse(BaseNodeModel):
    """Standard response for MCP tools."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    format: OutputFormat = "json"