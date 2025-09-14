from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer

from app.models.auth import LoginRequest, TokenResponse, ChangePasswordRequest, UserInfo
from app.services.auth_service import auth_service
from app.core.auth import get_current_user
from app.models.action_log import ActionType


class AuthController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/login", self.login, methods=["POST"], response_model=TokenResponse)
        self.router.add_api_route("/logout", self.logout, methods=["POST"])
        self.router.add_api_route("/me", self.get_current_user_info, methods=["GET"], response_model=UserInfo)
        self.router.add_api_route("/change-password", self.change_password, methods=["POST"])

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """
        Аутентификация пользователя.
        
        - **username**: Имя пользователя
        - **password**: Пароль
        
        Возвращает JWT токен для доступа к защищенным эндпоинтам.
        """
        try:
            user = auth_service.authenticate_user(login_data.username, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверные учетные данные",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = auth_service.create_access_token_for_user(user)
            
            
            return TokenResponse(**token_data)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при аутентификации"
            )

    async def logout(self, current_user: UserInfo = Depends(get_current_user)):
        """
        Выход из системы.
        
        В текущей реализации с JWT токенами, логаут работает на стороне клиента.
        Сервер только логирует событие выхода.
        
        Для полноценного логаута на сервере потребуется черный список токенов.
        """
        try:
            
            return {
                "message": "Успешный выход из системы",
                "note": "Удалите токен из клиентского приложения"
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при выходе из системы"
            )

    async def get_current_user_info(self, current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
        """
        Получение информации о текущем пользователе.
        
        Возвращает информацию о пользователе из JWT токена.
        Требует валидный JWT токен в заголовке Authorization.
        """
        return current_user

    async def change_password(
        self, 
        password_data: ChangePasswordRequest,
        current_user: UserInfo = Depends(get_current_user)
    ):
        """
        Смена пароля текущего пользователя.
        
        - **current_password**: Текущий пароль
        - **new_password**: Новый пароль
        
        Требует валидный JWT токен в заголовке Authorization.
        """
        try:
            success = auth_service.change_password(
                user_id=current_user.id,
                current_password=password_data.current_password,
                new_password=password_data.new_password
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не удалось изменить пароль. Проверьте текущий пароль."
                )
            
            
            return {
                "message": "Пароль успешно изменен"
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при смене пароля"
            )


router = AuthController().router