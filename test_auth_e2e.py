import asyncio
from careintel.core.config import get_settings
from careintel.core.database import build_engine, build_session_factory, dispose_engine
from careintel.application.auth.auth_service import AuthService
from careintel.application.auth.password_hasher import PasswordHasher
from careintel.application.auth.token_service import JWTService
from careintel.persistence.repositories.user_repo import UserRepository
from careintel.persistence.repositories.session_repo import SessionRepository
from careintel.persistence.repositories.audit_repo import AuditRepository

async def test():
    s = get_settings()
    e = build_engine(s)
    sf = build_session_factory(e)
    
    async with sf() as session:
        svc = AuthService(
            user_repo=UserRepository(session),
            session_repo=SessionRepository(session),
            audit_repo=AuditRepository(session),
            token_service=JWTService(s),
            hasher=PasswordHasher(),
        )
        token, user = await svc.login('doctor@careintel.local', 'demo123', 'test-corr')
        print('[OK] Generated JWT Token:', token[:30] + '...')
        print(f'[OK] Login User ID: {user.id}, Roles: {user.roles}, Permissions count: {len(user.permissions)}')
        user_val = await svc.get_current_user(token)
        print(f'[OK] Validated User ID: {user_val.id}, Roles: {user_val.roles}, Permissions count: {len(user_val.permissions)}')
        await session.commit()
        
    await dispose_engine(e)
    print('[OK] All end-to-end database auth checks passed!')

if __name__ == '__main__':
    asyncio.run(test())
