from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserSetting, TransportType
from ..schemas import UserSettingResponse, UserSettingBase, ModelListResponse

router = APIRouter(prefix="/settings", tags=["settings"])

def get_current_user_settings(user_id: int, db: Session) -> UserSetting:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    if not setting:
        # Should be created during user registration, but fallback just in case
        setting = UserSetting(user_id=user_id, mcp_transport=TransportType.stdio)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

@router.get("/", response_model=UserSettingResponse)
def get_settings(x_user_id: int = Header(...), db: Session = Depends(get_db)):
    return get_current_user_settings(x_user_id, db)

@router.put("/", response_model=UserSettingResponse)
def update_settings(settings_update: UserSettingBase, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    setting = get_current_user_settings(x_user_id, db)
    
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(setting, key, value)
        
    db.commit()
    db.refresh(setting)
    return setting

@router.get("/models", response_model=ModelListResponse)
async def get_available_models(
    provider: str = None, 
    x_user_id: int = Header(...), 
    db: Session = Depends(get_db)
):
    setting = get_current_user_settings(x_user_id, db)
    
    target_provider = provider or setting.ai_provider
    if not target_provider:
        raise HTTPException(status_code=400, detail="AI provider not specified in query or user settings")
    
    from ..ai.factory import get_ai_provider
    ai = get_ai_provider(provider_name=target_provider)
    models = await ai.get_models()
    return ModelListResponse(models=models)
