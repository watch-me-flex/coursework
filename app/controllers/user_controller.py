from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List

from app.models.user import User, UserCreate, UserUpdate, UserInDB
from app.models.auth import CreateUserRequest, UserInfo
from app.services.user_service import user_service
from app.core.auth import require_admin, get_current_user
from app.models.action_log import ActionType


class UserController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/", self.create_user, methods=["POST"], response_model=UserInDB, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/", self.get_users, methods=["GET"], response_model=List[UserInDB], dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}", self.get_user, methods=["GET"], response_model=UserInDB, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}", self.update_user, methods=["PUT"], response_model=UserInDB, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}", self.delete_user, methods=["DELETE"], dependencies=[Depends(require_admin)])

    async def create_user(
        self, 
        user_data: CreateUserRequest,
        current_user: UserInfo = Depends(require_admin)
    ) -> UserInDB:
        try:
            user = user_service.create(
                username=user_data.username,
                password=user_data.password,
                role_id=user_data.role_id,
                full_name=user_data.full_name
            )
            return user
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании пользователя")

    async def get_users(
        self,
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
        current_user: UserInfo = Depends(require_admin)
    ) -> List[UserInDB]:
        try:
            users = user_service.get_all(skip=skip, limit=limit)
            return users
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка пользователей")

    async def get_user(
        self, 
        user_id: int,
        current_user: UserInfo = Depends(require_admin)
    ) -> UserInDB:
        try:
            user = user_service.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
            return user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных пользователя")

    async def update_user(
        self, 
        user_id: int, 
        user_data: UserUpdate,
        current_user: UserInfo = Depends(require_admin)
    ) -> UserInDB:
        try:
            user = user_service.update(user_id, **user_data.dict(exclude_unset=True))
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
            return user
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении данных пользователя")

    async def delete_user(
        self, 
        user_id: int,
        current_user: UserInfo = Depends(require_admin)
    ):
        try:
            if user_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Нельзя удалить самого себя"
                )
            
            success = user_service.delete(user_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
            return {"message": "Пользователь успешно удален"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении пользователя")


router = UserController().router