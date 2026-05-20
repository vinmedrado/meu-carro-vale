from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

bearer = HTTPBearer()

def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
        sub = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user
