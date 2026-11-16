from fastapi import Depends, HTTPException, status

from models.user import User
from utils.dependencies import get_current_user


ROLES = {
    "SUPER_ADMIN",
    "ADMIN",
    "PRODUCT_MANAGER",
    "INVENTORY_MANAGER",
    "ORDER_MANAGER",
    "SUPPORT_AGENT",
    "CUSTOMER",
    "DELIVERY_MANAGER",
    "FINANCE_MANAGER",
}


def require_roles(*allowed_roles: str):
    invalid_roles = set(allowed_roles) - ROLES

    if invalid_roles:
        raise ValueError(f"Invalid roles: {', '.join(sorted(invalid_roles))}")

    def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker
