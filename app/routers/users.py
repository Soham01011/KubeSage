from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserSetting, TransportType
from ..schemas import UserResponse, UserCreate

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = User(username=user.username, usergroup=user.usergroup)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize empty settings for the new user
    default_settings = UserSetting(
        user_id=new_user.id,
        mcp_transport=TransportType.stdio
    )
    db.add(default_settings)
    db.commit()
    
    return new_user

@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
