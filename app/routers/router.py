from fastapi import APIRouter
from app.controllers.auth_controller import AuthController
from app.controllers.user_controller import UserController
from app.controllers.guest_controller import GuestController
from app.controllers.room_controller import RoomController
from app.controllers.checkin_controller import CheckInController
from app.controllers.payment_controller import PaymentController
from app.controllers.service_controller import ServiceController
from app.controllers.action_log_controller import ActionLogController

router = APIRouter()

auth_controller = AuthController()
user_controller = UserController()
guest_controller = GuestController()
room_controller = RoomController()
checkin_controller = CheckInController()
payment_controller = PaymentController()
service_controller = ServiceController()
action_log_controller = ActionLogController()

router.include_router(auth_controller.router, prefix="/auth", tags=["Аутентификация"])
router.include_router(user_controller.router, prefix="/users", tags=["Пользователи"])
router.include_router(guest_controller.router, prefix="/guests", tags=["Постояльцы"])
router.include_router(room_controller.router, prefix="/rooms", tags=["Номера"])
router.include_router(checkin_controller.router, prefix="/check-ins", tags=["Заселения"])
router.include_router(payment_controller.router, prefix="/payments", tags=["Платежи"])
router.include_router(service_controller.router, prefix="/services", tags=["Услуги"])
router.include_router(action_log_controller.router, prefix="/action-logs", tags=["Журнал событий"])

__all__ = ["router"]
