from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleName
from app.schemas.auth import UserOut
from app.api.deps import require_roles

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(role: RoleName | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    query = db.query(User)
    if role:
        query = query.join(User.role).filter_by(name=role)
    users = query.all()
    return [UserOut(id=u.id, full_name=u.full_name, email=u.email, role=u.role.name, is_active=u.is_active) for u in users]
