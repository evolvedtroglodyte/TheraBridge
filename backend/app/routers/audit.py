"""
Audit log endpoints for HIPAA compliance reporting.
Provides query, export, and patient accounting of disclosures.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta
import csv
import io

from app.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.models.security_models import AuditLog
from app.models.db_models import User
from app.schemas.audit_schemas import AuditLogQuery, AuditLogResponse, AuditLogEntry
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.get("/logs", response_model=AuditLogResponse)
@limiter.limit("50/minute")
async def get_audit_logs(
    request: Request,
    user_id: Optional[UUID] = Query(None, description="Filter by user who performed action"),
    patient_id: Optional[UUID] = Query(None, description="Filter by affected patient"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (normal, elevated, high)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated audit logs with filtering.

    Admin-only endpoint for querying audit log entries with comprehensive filtering
    options for HIPAA compliance investigations and reporting.

    Auth:
        Requires admin role

    Rate Limit:
        50 requests per minute per IP address

    Query Parameters:
        user_id: Filter by user who performed the action
        patient_id: Filter by affected patient
        action: Filter by action type (e.g., "record_view", "record_update")
        resource_type: Filter by resource type (e.g., "session", "note")
        start_date: Filter events after this timestamp
        end_date: Filter events before this timestamp
        risk_level: Filter by risk level (normal, elevated, high)
        page: Page number (1-indexed, default: 1)
        per_page: Results per page (default: 50, max: 200)

    Returns:
        AuditLogResponse with paginated entries and metadata

    Raises:
        HTTPException 403: If user is not an admin
        HTTPException 429: Rate limit exceeded
    """
    # Build query with filters
    query = select(AuditLog)

    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if patient_id:
        query = query.where(AuditLog.patient_id == patient_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    if risk_level:
        query = query.where(AuditLog.risk_level == risk_level)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()

    # Apply ordering and pagination
    offset = (page - 1) * per_page
    query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    # Convert to response schema
    entries = []
    for log in logs:
        # Get user email if user_id exists
        user_email = None
        user_role = None
        if log.user_id:
            user_query = select(User).where(User.id == log.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            if user:
                user_email = user.email
                user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)

        entry = AuditLogEntry(
            id=log.id,
            event_type=log.action,
            severity=log.risk_level,
            outcome="success" if log.response_status and 200 <= log.response_status < 300 else "failure",
            timestamp=log.timestamp,
            user_id=log.user_id,
            user_email=user_email,
            user_role=user_role,
            patient_id=log.patient_id,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            session_id=log.session_id,
            description=f"{log.action} on {log.resource_type}",
            metadata=log.details,
            changes=None
        )
        entries.append(entry)

    return AuditLogResponse(
        entries=entries,
        total_count=total_count,
        limit=per_page,
        offset=offset,
        has_more=offset + per_page < total_count
    )


@router.get("/logs/export")
@limiter.limit("5/minute")
async def export_audit_logs(
    request: Request,
    user_id: Optional[UUID] = Query(None, description="Filter by user who performed action"),
    patient_id: Optional[UUID] = Query(None, description="Filter by affected patient"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (normal, elevated, high)"),
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Export audit logs to CSV file.

    Admin-only endpoint for exporting audit logs matching filter criteria.
    Generates a CSV file for compliance reporting and archival purposes.

    Auth:
        Requires admin role

    Rate Limit:
        5 requests per minute per IP address (export operations are resource-intensive)

    Query Parameters:
        Same filters as /logs endpoint (without pagination)

    Returns:
        StreamingResponse: CSV file download
        Filename: audit_logs_{timestamp}.csv
        Columns: timestamp, user_email, action, resource_type, resource_id,
                 patient_name, ip_address, risk_level

    Raises:
        HTTPException 403: If user is not an admin
        HTTPException 429: Rate limit exceeded
    """
    # Build query with same filters as get_audit_logs
    query = select(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if patient_id:
        query = query.where(AuditLog.patient_id == patient_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    if risk_level:
        query = query.where(AuditLog.risk_level == risk_level)

    # Order by timestamp descending
    query = query.order_by(AuditLog.timestamp.desc())

    # Execute query (no pagination for export)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'timestamp',
        'user_email',
        'action',
        'resource_type',
        'resource_id',
        'patient_name',
        'ip_address',
        'risk_level'
    ])

    # Write data rows
    for log in logs:
        # Get user email
        user_email = ""
        if log.user_id:
            user_query = select(User).where(User.id == log.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            if user:
                user_email = user.email

        # Get patient name
        patient_name = ""
        if log.patient_id:
            patient_query = select(User).where(User.id == log.patient_id)
            patient_result = await db.execute(patient_query)
            patient = patient_result.scalar_one_or_none()
            if patient:
                # Use full_name if available, otherwise combine first and last
                if hasattr(patient, 'first_name') and hasattr(patient, 'last_name'):
                    patient_name = f"{patient.first_name} {patient.last_name}"
                elif hasattr(patient, 'full_name'):
                    patient_name = patient.full_name

        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else '',
            user_email,
            log.action or '',
            log.resource_type or '',
            str(log.resource_id) if log.resource_id else '',
            patient_name,
            log.ip_address or '',
            log.risk_level or ''
        ])

    # Prepare file for download
    output.seek(0)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_logs_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/patients/{patient_id}/accounting")
@limiter.limit("30/minute")
async def get_patient_accounting_of_disclosures(
    request: Request,
    patient_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for accounting period"),
    end_date: Optional[datetime] = Query(None, description="End date for accounting period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get HIPAA accounting of disclosures for a patient.

    Returns a list of all PHI access events for a specific patient, excluding
    the patient's own access and treatment/payment/operations activities.
    This endpoint satisfies the HIPAA right to an accounting of disclosures.

    Auth:
        Requires authentication
        User must be admin OR the patient themselves

    Rate Limit:
        30 requests per minute per IP address

    Path Parameters:
        patient_id: UUID of the patient

    Query Parameters:
        start_date: Start of accounting period (default: 6 years ago per HIPAA)
        end_date: End of accounting period (default: now)

    Returns:
        List of disclosure records with timestamp, accessor, purpose, and details

    Raises:
        HTTPException 403: If user is not admin and not the patient
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    HIPAA Compliance:
        - Covers 6 years of disclosure history by default
        - Excludes patient's own access
        - Excludes treatment, payment, and healthcare operations
        - Includes disclosure purpose and recipient information
    """
    # Authorization check: user must be admin OR the patient themselves
    is_admin = current_user.role.value == "admin" if hasattr(current_user.role, 'value') else current_user.role == "admin"
    is_patient = current_user.id == patient_id

    if not (is_admin or is_patient):
        raise HTTPException(
            status_code=403,
            detail="Access denied. You can only view your own accounting of disclosures."
        )

    # Verify patient exists
    patient_query = select(User).where(User.id == patient_id)
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Set default date range (6 years per HIPAA requirement)
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=6*365)

    # Query for PHI access events
    # Exclude:
    # 1. Patient's own access
    # 2. Treatment/payment/operations (actions: record_view, record_create, record_update during normal therapy)
    #
    # Include:
    # - External exports
    # - Third-party access
    # - Emergency access
    # - Administrative access not part of direct treatment

    query = select(AuditLog).where(
        and_(
            AuditLog.patient_id == patient_id,
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date,
            AuditLog.user_id != patient_id,  # Exclude patient's own access
            or_(
                AuditLog.action == 'export_data',
                AuditLog.action == 'emergency_access_granted',
                AuditLog.resource_type == 'external_disclosure'
            )
        )
    ).order_by(AuditLog.timestamp.desc())

    result = await db.execute(query)
    disclosures = result.scalars().all()

    # Format response
    accounting_records = []
    for disclosure in disclosures:
        # Get accessor information
        accessor_email = ""
        accessor_role = ""
        if disclosure.user_id:
            user_query = select(User).where(User.id == disclosure.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            if user:
                accessor_email = user.email
                accessor_role = user.role.value if hasattr(user.role, 'value') else str(user.role)

        record = {
            "id": str(disclosure.id),
            "timestamp": disclosure.timestamp.isoformat() if disclosure.timestamp else None,
            "action": disclosure.action,
            "accessor_email": accessor_email,
            "accessor_role": accessor_role,
            "resource_type": disclosure.resource_type,
            "resource_id": str(disclosure.resource_id) if disclosure.resource_id else None,
            "purpose": disclosure.details.get("purpose") if disclosure.details else "Not specified",
            "recipient": disclosure.details.get("recipient") if disclosure.details else "Internal",
            "ip_address": disclosure.ip_address,
            "details": disclosure.details
        }
        accounting_records.append(record)

    return {
        "patient_id": str(patient_id),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_disclosures": len(accounting_records),
        "disclosures": accounting_records,
        "hipaa_notice": "This accounting includes disclosures of your health information made by this practice, excluding disclosures for treatment, payment, healthcare operations, and disclosures you authorized."
    }
