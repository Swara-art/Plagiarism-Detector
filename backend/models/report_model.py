from pydantic import BaseModel
from typing import List, Optional

class FlaggedSection(BaseModel):
    start: int
    end: int
    match_score: float
    matched_source: str
    reason: str

class FlaggedBlock(BaseModel):
    lines: str
    match_score: float
    matched_source: str
    reason: str

class OriginalityReport(BaseModel):
    submission_id: str
    filename: str
    originality_score: float
    plagiarism_score: float
    flagged_sections: List[FlaggedSection] = []
    citations: List[str] = []
    summary: str

class CodeReport(BaseModel):
    submission_id: str
    filename: str
    language: str
    originality_score: float
    plagiarism_score: float
    flagged_blocks: List[FlaggedBlock] = []
    summary: str