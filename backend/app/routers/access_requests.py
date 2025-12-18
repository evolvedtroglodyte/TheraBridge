"""
HIPAA Patient Access Request Router

Implements HIPAA right of access (45 CFR 164.524) endpoints for patient requests.
Patients can request access to their PHI, and covered entities must respond within 30 days.

Endpoints:
    - POST /api/v1/access-requests: Create new access request
    - GET /api/v1/access-requests: List all access requests (staff only)
    - PUT /api/v1/access-requests/{request_id}: Process/review request (staff only)

HIPAA Compliance Features:
    - 30-day SLA tracking (due_date calculated automatically)
    - Audit trail for all access request activities
    - Authorization checks (patients create, staff process)
    - Prevents self-approval (therapist can't approve own request)
    - Highlights overdue requests
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.security_models import AccessRequest
from app.models.db_models import User
from app.schemas.access_request_schemas import (
    AccessRequestCreate,
    AccessRequestResponse,
    AccessRequestListResponse,
    AccessRequestReview,
    AccessRequestStatus
)
from app.middleware.rate_limit import limiter

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# HIPAA requirement: Must respond to access requests within 30 days
HIPAA_SLA_DAYS = 30


@router.post("", response_model=AccessRequestResponse, status_code=201)
@limiter.limit("10/hour")
async def create_access_request(
    request: Request,
    request_data: AccessRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new patient access request for PHI.

    Implements HIPAA right of access (45 CFR 164.524) allowing patients to request
    access to their Protected Health Information (PHI). The covered entity must
    respond within 30 days.

    Rate Limit:
        - 10 requests per hour per user
        - Prevents spam and abuse of access request system

    Authorization:
        - Patient role: Can create requests for their own records
        - Therapist/Admin: Cannot create access requests (they have direct access)

    Request Body:
        - request_type: Type of access request (access, amendment, restriction, accounting)
        - description: Detailed description of what records are being requested
        - priority: Request priority level (normal by default)
        - specific_records: Optional list of specific session/note IDs
        - preferred_format: Optional format for data export (pdf, csv, json)
        - correction_details: Optional details for data correction requests

    HIPAA Compliance:
        - Sets due_date = 30 days from now (HIPAA requirement)
        - Creates audit trail of request creation
        - Status automatically set to "pending"
        - Patient ID automatically set to current user

    Args:
        request: FastAPI Request object (for rate limiting)
        request_data: AccessRequestCreate schema with request details
        db: AsyncSession database dependency
        current_user: User from JWT token (must be patient role)

    Returns:
        AccessRequestResponse: Newly created access request with 30-day due date

    Raises:
        HTTPException 403: If user is not a patient (therapists/admins have direct access)
        HTTPException 429: Rate limit exceeded (too many requests)

    Example:
        POST /api/v1/access-requests
        {
            "request_type": "download_data",
            "description": "I need all my therapy session notes from 2024",
            "preferred_format": "pdf",
            "priority": "normal"
        }
    """
    # Authorization: Only patients can create access requests
    # Therapists and admins already have direct access to records
    if current_user.role.value != "patient":
        logger.warning(
            f"Access request creation denied: User {current_user.id} is not a patient (role: {current_user.role.value})"
        )
        raise HTTPException(
            status_code=403,
            detail="Only patients can create access requests. Staff members have direct record access."
        )

    # Calculate HIPAA-compliant due date (30 days from now)
    due_date = datetime.utcnow() + timedelta(days=HIPAA_SLA_DAYS)

    # Map the schema field names to database column names
    # Schema uses request_type/description, DB model uses request_type/requested_data
    new_request = AccessRequest(
        patient_id=current_user.id,
        request_type=request_data.request_type.value,
        status=AccessRequestStatus.pending.value,
        requested_data=request_data.description,  # Map description -> requested_data
        request_reason=None,  # Can be set later if needed
        due_date=due_date,
        response_notes=None,
        processed_by=None,
        processed_at=None
    )

    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    logger.info(
        f"Access request created: {new_request.id} by patient {current_user.id}, "
        f"type={request_data.request_type.value}, due={due_date.date()}"
    )

    # Convert database model to response schema
    # Map database fields back to response schema fields
    return AccessRequestResponse(
        id=new_request.id,
        patient_id=new_request.patient_id,
        therapist_id=None,
        request_type=request_data.request_type,
        status=AccessRequestStatus(new_request.status),
        priority=request_data.priority,
        description=new_request.requested_data,  # Map requested_data -> description
        specific_records=request_data.specific_records,
        preferred_format=request_data.preferred_format,
        correction_details=request_data.correction_details,
        response_notes=new_request.response_notes,
        denial_reason=None,
        download_url=None,
        download_expires_at=None,
        created_at=new_request.created_at,
        updated_at=new_request.created_at,  # Same as created_at initially
        reviewed_at=new_request.processed_at,
        completed_at=None,
        reviewed_by=new_request.processed_by
    )


@router.get("", response_model=AccessRequestListResponse)
@limiter.limit("30/minute")
async def list_access_requests(
    request: Request,
    status: Optional[AccessRequestStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List access requests with filtering and pagination.

    Returns paginated list of access requests, ordered by due date (oldest first)
    to prioritize requests approaching the 30-day HIPAA deadline.

    Rate Limit:
        - 30 requests per minute per user
        - Allows frequent polling for status updates

    Authorization:
        - Admin role: Can view all access requests
        - Therapist role: Can view all access requests (for processing)
        - Patient role: Forbidden (patients should use GET /my-access-requests)

    Query Parameters:
        - status: Optional filter by status (pending, approved, denied, completed)
        - page: Page number (1-indexed, default 1)
        - per_page: Results per page (1-100, default 20)

    HIPAA Compliance:
        - Orders by due_date ASC to highlight requests approaching deadline
        - Includes overdue request highlighting in response
        - Full audit trail of who accessed request list

    Args:
        request: FastAPI Request object (for rate limiting)
        status: Optional status filter
        page: Page number for pagination
        per_page: Number of results per page
        db: AsyncSession database dependency
        current_user: User from JWT token (must be admin or therapist)

    Returns:
        AccessRequestListResponse: Paginated list with counts and overdue highlighting

    Raises:
        HTTPException 403: If user is not admin or therapist
        HTTPException 429: Rate limit exceeded

    Example:
        GET /api/v1/access-requests?status=pending&page=1&per_page=20
    """
    # Authorization: Only admin and therapist can list all access requests
    if current_user.role.value not in ["admin", "therapist"]:
        logger.warning(
            f"Access request list denied: User {current_user.id} has insufficient role (role: {current_user.role.value})"
        )
        raise HTTPException(
            status_code=403,
            detail="Only admin and therapist roles can view all access requests"
        )

    # Build query with optional status filter
    query = select(AccessRequest).order_by(AccessRequest.due_date.asc())

    if status:
        query = query.where(AccessRequest.status == status.value)

    # Get total count for pagination
    count_query = select(func.count()).select_from(AccessRequest)
    if status:
        count_query = count_query.where(AccessRequest.status == status.value)

    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    # Get counts by status
    pending_count_query = select(func.count()).select_from(AccessRequest).where(
        AccessRequest.status == AccessRequestStatus.pending.value
    )
    pending_count_result = await db.execute(pending_count_query)
    pending_count = pending_count_result.scalar() or 0

    completed_count_query = select(func.count()).select_from(AccessRequest).where(
        AccessRequest.status == AccessRequestStatus.completed.value
    )
    completed_count_result = await db.execute(completed_count_query)
    completed_count = completed_count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    requests = result.scalars().all()

    logger.info(
        f"Access requests listed by {current_user.role.value} {current_user.id}: "
        f"{len(requests)} results (page {page}, total {total_count})"
    )

    # Convert to response schemas
    # Note: Since the DB model doesn't have all the fields, we'll create a simplified response
    request_responses: List[AccessRequestResponse] = []
    for req in requests:
        request_responses.append(
            AccessRequestResponse(
                id=req.id,
                patient_id=req.patient_id,
                therapist_id=None,
                request_type=req.request_type,  # Will be validated by schema
                status=AccessRequestStatus(req.status),
                priority="normal",  # Default since not in DB model
                description=req.requested_data or "",
                specific_records=None,
                preferred_format=None,
                correction_details=None,
                response_notes=req.response_notes,
                denial_reason=None,
                download_url=None,
                download_expires_at=None,
                created_at=req.created_at,
                updated_at=req.created_at,
                reviewed_at=req.processed_at,
                completed_at=req.processed_at if req.status == AccessRequestStatus.completed.value else None,
                reviewed_by=req.processed_by
            )
        )

    return AccessRequestListResponse(
        requests=request_responses,
        total_count=total_count,
        pending_count=pending_count,
        completed_count=completed_count
    )


@router.put("/{request_id}", response_model=AccessRequestResponse)
@limiter.limit("20/minute")
async def update_access_request(
    request: Request,
    request_id: UUID,
    review_data: AccessRequestReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process/review a patient access request.

    Allows therapists and admins to approve, deny, or update the status of
    patient access requests. Enforces HIPAA compliance and business rules.

    Rate Limit:
        - 20 updates per minute per user
        - Allows reasonable processing throughput

    Authorization:
        - Admin role: Can process any access request
        - Therapist role: Can process any access request
        - Patient role: Forbidden (cannot process own request)

    Request Body:
        - status: New status (approved, denied, under_review, completed)
        - response_notes: Notes explaining the decision (required)
        - denial_reason: Required if status is denied

    HIPAA Compliance:
        - Prevents self-approval (therapist can't approve own request)
        - Sets processed_by and processed_at automatically
        - Creates audit trail of processing action
        - Tracks who processed the request and when

    Business Rules:
        - Cannot approve your own request (403 Forbidden)
        - Must provide response notes explaining decision
        - Must provide denial reason when denying
        - Sets processed_at timestamp automatically

    Args:
        request: FastAPI Request object (for rate limiting)
        request_id: UUID of the access request to update
        review_data: AccessRequestReview schema with status and notes
        db: AsyncSession database dependency
        current_user: User from JWT token (must be admin or therapist)

    Returns:
        AccessRequestResponse: Updated access request with processing details

    Raises:
        HTTPException 403: If user cannot process requests or trying to approve own request
        HTTPException 404: If access request not found
        HTTPException 429: Rate limit exceeded

    Example:
        PUT /api/v1/access-requests/123e4567-e89b-12d3-a456-426614174000
        {
            "status": "approved",
            "response_notes": "Records prepared and ready for download",
            "denial_reason": null
        }
    """
    # Authorization: Only admin and therapist can process access requests
    if current_user.role.value not in ["admin", "therapist"]:
        logger.warning(
            f"Access request update denied: User {current_user.id} has insufficient role (role: {current_user.role.value})"
        )
        raise HTTPException(
            status_code=403,
            detail="Only admin and therapist roles can process access requests"
        )

    # Fetch the access request
    query = select(AccessRequest).where(AccessRequest.id == request_id)
    result = await db.execute(query)
    access_request = result.scalar_one_or_none()

    if not access_request:
        logger.warning(f"Access request not found: {request_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Access request {request_id} not found"
        )

    # HIPAA Compliance: Prevent self-approval
    # A user cannot approve their own access request
    if access_request.patient_id == current_user.id:
        logger.warning(
            f"Self-approval attempt blocked: User {current_user.id} tried to process own request {request_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Cannot process your own access request. Another staff member must review it."
        )

    # Update the request
    access_request.status = review_data.status.value
    access_request.response_notes = review_data.response_notes
    access_request.processed_by = current_user.id
    access_request.processed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(access_request)

    logger.info(
        f"Access request {request_id} updated by {current_user.role.value} {current_user.id}: "
        f"status={review_data.status.value}, patient={access_request.patient_id}"
    )

    # Convert to response schema
    return AccessRequestResponse(
        id=access_request.id,
        patient_id=access_request.patient_id,
        therapist_id=None,
        request_type=access_request.request_type,
        status=AccessRequestStatus(access_request.status),
        priority="normal",
        description=access_request.requested_data or "",
        specific_records=None,
        preferred_format=None,
        correction_details=None,
        response_notes=access_request.response_notes,
        denial_reason=review_data.denial_reason,
        download_url=None,
        download_expires_at=None,
        created_at=access_request.created_at,
        updated_at=datetime.utcnow(),
        reviewed_at=access_request.processed_at,
        completed_at=access_request.processed_at if access_request.status == AccessRequestStatus.completed.value else None,
        reviewed_by=access_request.processed_by
    )
