# backend/src/api/endpoints/fraud_cases.py

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from backend.src.api.dependencies import get_current_user, get_db_context
from backend.src.api.schemas.fraud_case_schemas import (
    FraudCaseCreate, FraudCaseResponse, FraudCaseUpdate,
    FraudConfirmationCreate, FraudCaseFilter
)
from backend.src.domain.services.fraud_case_service import FraudCaseService
from backend.src.infrastructure.persistence.db_context import FraudDetectionDbContext
from backend.src.infrastructure.persistence.models import User

router = APIRouter()


@router.get("/", response_model=List[FraudCaseResponse])
async def get_fraud_cases(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    client_code: Optional[str] = Query(None, description="Filter by client code"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Get list of fraud cases with optional filters."""
    service = FraudCaseService(db)
    
    filters = FraudCaseFilter(
        status=status_filter,
        severity=severity,
        client_code=client_code,
        date_from=date_from,
        date_to=date_to
    )
    
    cases = service.get_fraud_cases(filters, skip, limit)
    return cases


@router.get("/{case_id}", response_model=FraudCaseResponse)
async def get_fraud_case(
    case_id: int,
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Get a specific fraud case by ID."""
    service = FraudCaseService(db)
    case = service.get_fraud_case_by_id(case_id)
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fraud case {case_id} not found"
        )
    
    return case


@router.post("/", response_model=FraudCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_fraud_case(
    fraud_case: FraudCaseCreate,
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Create a new fraud case manually."""
    service = FraudCaseService(db)
    
    try:
        new_case = service.create_fraud_case(fraud_case, current_user.id)
        return new_case
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{case_id}", response_model=FraudCaseResponse)
async def update_fraud_case(
    case_id: int,
    fraud_case_update: FraudCaseUpdate,
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Update a fraud case."""
    service = FraudCaseService(db)
    
    try:
        updated_case = service.update_fraud_case(case_id, fraud_case_update, current_user.id)
        
        if not updated_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fraud case {case_id} not found"
            )
        
        return updated_case
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{case_id}/confirm", response_model=dict)
async def confirm_fraud_case(
    case_id: int,
    confirmation: FraudConfirmationCreate,
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Confirm or reject a fraud case."""
    service = FraudCaseService(db)
    
    try:
        result = service.confirm_fraud_case(
            case_id,
            confirmation,
            current_user.id
        )
        
        return {
            "message": "Fraud case confirmation recorded",
            "case_id": case_id,
            "decision": confirmation.decision,
            "new_status": result.status.value
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{case_id}/related", response_model=List[dict])
async def get_related_transactions(
    case_id: int,
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Get transactions related to a fraud case."""
    service = FraudCaseService(db)
    
    try:
        related = service.get_related_transactions(case_id)
        return related
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/statistics/summary", response_model=dict)
async def get_fraud_statistics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Get fraud statistics summary."""
    service = FraudCaseService(db)
    
    stats = service.get_statistics(date_from, date_to)
    return stats


@router.post("/{case_id}/escalate", response_model=dict)
async def escalate_fraud_case(
    case_id: int,
    reason: str = Query(..., description="Reason for escalation"),
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Escalate a fraud case to higher authority."""
    service = FraudCaseService(db)
    
    try:
        result = service.escalate_case(case_id, reason, current_user.id)
        return {
            "message": "Case escalated successfully",
            "case_id": case_id,
            "new_status": result.status.value
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fraud_case(
    case_id: int,
    db: FraudDetectionDbContext = Depends(get_db_context),
    current_user: User = Depends(get_current_user)
):
    """Delete a fraud case (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete fraud cases"
        )
    
    service = FraudCaseService(db)
    
    if not service.delete_fraud_case(case_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fraud case {case_id} not found"
        )
    
    return None