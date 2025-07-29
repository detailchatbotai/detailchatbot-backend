"""
Service management router for handling shop service catalog operations.
Provides CRUD endpoints for managing detailing services and pricing.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_user_shop, rate_limit_general, UserShop
from app.models.service import Service
from app.schemas.service import (
    ServiceCreateRequest,
    ServiceUpdateRequest,
    ServiceResponse,
    ServiceListResponse,
    MessageResponse
)

router = APIRouter()


def format_service_response(service: Service) -> ServiceResponse:
    """Format service object for API response"""
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        price=service.price,
        duration_minutes=service.duration_minutes,
        is_active=service.is_active,
        is_addon=service.is_addon,
        shop_id=service.shop_id,
        created_at=service.created_at.isoformat() if service.created_at else None,
        updated_at=service.updated_at.isoformat() if service.updated_at else None
    )


@router.get(
    "/",
    response_model=ServiceListResponse,
    summary="Get shop services",
    description="Get list of all services for the current shop"
)
async def get_services(
    shop: UserShop,
    include_inactive: bool = Query(False, description="Include inactive services"),
    addons_only: bool = Query(False, description="Return only add-on services"),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get list of all services for the current shop"""
    try:
        query = db.query(Service).filter(Service.shop_id == shop.id)
        
        if not include_inactive:
            query = query.filter(Service.is_active == True)
            
        if addons_only:
            query = query.filter(Service.is_addon == True)
            
        services = query.order_by(Service.name).all()
        
        service_responses = [format_service_response(service) for service in services]
        
        # Calculate stats
        total_services = len(service_responses)
        active_count = len([s for s in service_responses if s.is_active])
        addon_count = len([s for s in service_responses if s.is_addon])
        
        return ServiceListResponse(
            services=service_responses,
            total=total_services,
            active_count=active_count,
            addon_count=addon_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve services"
        )


@router.post(
    "/",
    response_model=ServiceResponse,
    summary="Create service",
    description="Create a new service for the shop"
)
async def create_service(
    service_data: ServiceCreateRequest,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Create a new service for the shop"""
    try:
        # Check service limit based on plan
        plan = shop.plan
        if plan:
            current_service_count = db.query(Service).filter(Service.shop_id == shop.id).count()
            if current_service_count >= plan.max_services:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Service limit reached. Your plan allows {plan.max_services} services."
                )
        
        # Check for duplicate service name
        existing_service = db.query(Service).filter(
            Service.shop_id == shop.id,
            Service.name == service_data.name
        ).first()
        
        if existing_service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A service with this name already exists"
            )
        
        # Create new service
        new_service = Service(
            name=service_data.name,
            description=service_data.description,
            price=service_data.price,
            duration_minutes=service_data.duration_minutes,
            is_active=service_data.is_active,
            is_addon=service_data.is_addon,
            shop_id=shop.id
        )
        
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        
        return format_service_response(new_service)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service"
        )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get service",
    description="Get a specific service by ID"
)
async def get_service(
    service_id: int,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get a specific service by ID"""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.shop_id == shop.id
        ).first()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        return format_service_response(service)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service"
        )


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service",
    description="Update an existing service"
)
async def update_service(
    service_id: int,
    service_data: ServiceUpdateRequest,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Update an existing service"""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.shop_id == shop.id
        ).first()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        # Check for duplicate name if updating name
        if service_data.name and service_data.name != service.name:
            existing_service = db.query(Service).filter(
                Service.shop_id == shop.id,
                Service.name == service_data.name,
                Service.id != service_id
            ).first()
            
            if existing_service:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A service with this name already exists"
                )
        
        # Update fields
        update_data = service_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service, field, value)
        
        db.commit()
        db.refresh(service)
        
        return format_service_response(service)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update service"
        )


@router.delete(
    "/{service_id}",
    response_model=MessageResponse,
    summary="Delete service",
    description="Delete a service (soft delete by setting inactive)"
)
async def delete_service(
    service_id: int,
    shop: UserShop,
    permanent: bool = Query(False, description="Permanently delete instead of soft delete"),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Delete a service (soft delete by default, permanent if specified)"""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.shop_id == shop.id
        ).first()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        if permanent:
            # Permanent deletion
            db.delete(service)
            message = "Service permanently deleted"
        else:
            # Soft delete - just set as inactive
            service.is_active = False
            message = "Service deactivated"
        
        db.commit()
        
        return MessageResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete service"
        )


@router.post(
    "/{service_id}/activate",
    response_model=MessageResponse,
    summary="Activate service",
    description="Reactivate an inactive service"
)
async def activate_service(
    service_id: int,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Reactivate an inactive service"""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.shop_id == shop.id
        ).first()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        if service.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service is already active"
            )
        
        service.is_active = True
        db.commit()
        
        return MessageResponse(message="Service activated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate service"
        )