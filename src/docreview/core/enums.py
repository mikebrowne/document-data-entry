from enum import Enum


class DocumentType(str, Enum):
    PAYSTUB = "paystub"
    T4 = "t4"
    NOTICE_OF_ASSESSMENT = "notice_of_assessment"
    BANK_STATEMENT = "bank_statement"
    GOVERNMENT_ID = "government_id"
    UNKNOWN = "unknown"


class PipelineStage(str, Enum):
    INGEST = "ingest"
    EXTRACT = "extract"
    CLASSIFY = "classify"
    NORMALIZE = "normalize"
    VALIDATE = "validate"
    RENDER = "render"


class HandoffReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN_DOCUMENT_TYPE = "unknown_document_type"
    OCR_REQUIRED = "ocr_required"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_INPUT = "invalid_input"
    UNREADABLE_INPUT = "unreadable_input"
    PAGE_LIMIT_EXCEEDED = "page_limit_exceeded"


class HandoffAction(str, Enum):
    MANUAL_REVIEW = "manual_review"
    PROVIDE_CLEARER_DOCUMENT = "provide_clearer_document"
    PROVIDE_MISSING_INFORMATION = "provide_missing_information"
    FIX_INPUT = "fix_input"


class FieldStatus(str, Enum):
    PROPOSED = "proposed"
    VALID = "valid"
    MISSING = "missing"
    HANDOFF_REQUIRED = "handoff_required"
