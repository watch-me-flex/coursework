from typing import List, Optional
from datetime import date, datetime
from app.models.checkin import (
    CheckIn, CheckInCreate, CheckInUpdate, CheckInWithDetails,
    CheckOutRequest, CurrentGuestView, CheckInStatus
)
from app.db.database import DBSession


class CheckInService:
    
    @classmethod
    def check_in_guest(cls, guest_id: int, room_id: int, check_in_date: Optional[date] = None) -> CheckIn:
        if check_in_date is None:
            check_in_date = date.today()
            
        with DBSession() as db:
            db.execute("SELECT id FROM guests WHERE id = %s", (guest_id,))
            if not db.fetchone():
                raise ValueError(f"Постоялец с ID {guest_id} не найден")
            
            db.execute("SELECT capacity, is_available FROM rooms WHERE id = %s", (room_id,))
            room_info = db.fetchone()
            if not room_info:
                raise ValueError(f"Номер с ID {room_id} не найден")
            
            if not room_info['is_available']:
                raise ValueError("Номер недоступен для заселения")
            
            db.execute(
                "SELECT id FROM check_ins WHERE guest_id = %s AND status = %s",
                (guest_id, CheckInStatus.ACTIVE.value)
            )
            if db.fetchone():
                raise ValueError("Постоялец уже заселен в другой номер")
            
            db.execute(
                "SELECT COUNT(*) as current_guests FROM check_ins WHERE room_id = %s AND status = %s",
                (room_id, CheckInStatus.ACTIVE.value)
            )
            current_guests = db.fetchone()['current_guests']
            
            if current_guests >= room_info['capacity']:
                raise ValueError("В номере нет свободных мест")
            
            check_in_data = CheckInCreate(
                guest_id=guest_id,
                room_id=room_id,
                check_in_date=check_in_date,
                status=CheckInStatus.ACTIVE
            )
            
            db.execute(
                """
                INSERT INTO check_ins (guest_id, room_id, check_in_date, status)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (check_in_data.guest_id, check_in_data.room_id, 
                 check_in_data.check_in_date, check_in_data.status.value)
            )
            result = db.fetchone()
            return CheckIn(**result)

    @classmethod
    def check_out_guest(cls, check_out_request: CheckOutRequest) -> CheckIn:
        with DBSession() as db:
            db.execute(
                "SELECT * FROM check_ins WHERE id = %s AND status = %s",
                (check_out_request.check_in_id, CheckInStatus.ACTIVE.value)
            )
            check_in_record = db.fetchone()
            if not check_in_record:
                raise ValueError("Активное заселение не найдено")
            
            if check_out_request.check_out_date < check_in_record['check_in_date']:
                raise ValueError("Дата выселения не может быть раньше даты заселения")
            
            db.execute(
                """
                UPDATE check_ins 
                SET check_out_date = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *
                """,
                (check_out_request.check_out_date, CheckInStatus.COMPLETED.value, 
                 check_out_request.check_in_id)
            )
            result = db.fetchone()
            return CheckIn(**result)

    @classmethod
    def get_by_id(cls, check_in_id: int) -> Optional[CheckIn]:
        with DBSession() as db:
            db.execute("SELECT * FROM check_ins WHERE id = %s", (check_in_id,))
            result = db.fetchone()
            return CheckIn(**result) if result else None

    @classmethod
    def get_with_details(cls, check_in_id: int) -> Optional[CheckInWithDetails]:
        with DBSession() as db:
            db.execute(
                """
                SELECT ci.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       r.room_number,
                       rt.name as room_type,
                       r.price_per_night
                FROM check_ins ci
                JOIN guests g ON ci.guest_id = g.id
                JOIN rooms r ON ci.room_id = r.id
                JOIN room_types rt ON r.type_id = rt.id
                WHERE ci.id = %s
                """,
                (check_in_id,)
            )
            result = db.fetchone()
            return CheckInWithDetails(**result) if result else None

    @classmethod
    def get_current_guests(cls) -> List[CurrentGuestView]:
        with DBSession() as db:
            db.execute("SELECT * FROM view_current_guests ORDER BY room_number")
            results = db.fetchall()
            return [CurrentGuestView(**row) for row in results]

    @classmethod
    def get_guest_check_ins(cls, guest_id: int) -> List[CheckInWithDetails]:
        with DBSession() as db:
            db.execute(
                """
                SELECT ci.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       r.room_number,
                       rt.name as room_type,
                       r.price_per_night
                FROM check_ins ci
                JOIN guests g ON ci.guest_id = g.id
                JOIN rooms r ON ci.room_id = r.id
                JOIN room_types rt ON r.type_id = rt.id
                WHERE ci.guest_id = %s
                ORDER BY ci.check_in_date DESC
                """,
                (guest_id,)
            )
            results = db.fetchall()
            return [CheckInWithDetails(**row) for row in results]

    @classmethod
    def get_room_check_ins(cls, room_id: int) -> List[CheckInWithDetails]:
        with DBSession() as db:
            db.execute(
                """
                SELECT ci.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       r.room_number,
                       rt.name as room_type,
                       r.price_per_night
                FROM check_ins ci
                JOIN guests g ON ci.guest_id = g.id
                JOIN rooms r ON ci.room_id = r.id
                JOIN room_types rt ON r.type_id = rt.id
                WHERE ci.room_id = %s
                ORDER BY ci.check_in_date DESC
                """,
                (room_id,)
            )
            results = db.fetchall()
            return [CheckInWithDetails(**row) for row in results]

    @classmethod
    def get_all_check_ins(
        cls, 
        status: Optional[CheckInStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CheckInWithDetails]:
        with DBSession() as db:
            conditions = []
            params = []
            
            if status:
                conditions.append("ci.status = %s")
                params.append(status.value)
            
            if date_from:
                conditions.append("ci.check_in_date >= %s")
                params.append(date_from)
                
            if date_to:
                conditions.append("ci.check_in_date <= %s")
                params.append(date_to)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT ci.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       r.room_number,
                       rt.name as room_type,
                       r.price_per_night
                FROM check_ins ci
                JOIN guests g ON ci.guest_id = g.id
                JOIN rooms r ON ci.room_id = r.id
                JOIN room_types rt ON r.type_id = rt.id
                {where_clause}
                ORDER BY ci.check_in_date DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, skip])
            db.execute(query, tuple(params))
            results = db.fetchall()
            return [CheckInWithDetails(**row) for row in results]

    @classmethod
    def update(cls, check_in_id: int, check_in_data: CheckInUpdate) -> Optional[CheckIn]:
        if not any(v is not None for v in check_in_data.dict().values()):
            return None
            
        with DBSession() as db:
            db.execute("SELECT * FROM check_ins WHERE id = %s", (check_in_id,))
            existing = db.fetchone()
            if not existing:
                return None
                
            set_parts = []
            values = []

            update_dict = check_in_data.dict(exclude_unset=True, exclude_none=True)
            for key, value in update_dict.items():
                if key == 'status' and isinstance(value, CheckInStatus):
                    set_parts.append(f"{key} = %s")
                    values.append(value.value)
                else:
                    set_parts.append(f"{key} = %s")
                    values.append(value)
            
            if not set_parts:
                return None
                
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
                
            query = f"""
                UPDATE check_ins 
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
            """
            values.append(check_in_id)
            
            db.execute(query, tuple(values))
            result = db.fetchone()
            return CheckIn(**result) if result else None

    @classmethod
    def cancel_check_in(cls, check_in_id: int) -> Optional[CheckIn]:
        return cls.update(check_in_id, CheckInUpdate(status=CheckInStatus.CANCELLED))

    @classmethod
    def get_occupancy_statistics(cls, date_from: Optional[date] = None, date_to: Optional[date] = None) -> dict:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("ci.check_in_date >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("ci.check_in_date <= %s") 
                date_params.append(date_to)
            
            date_where = "AND " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT 
                    COUNT(*) as total_checkins,
                    COUNT(CASE WHEN status = 'Активно' THEN 1 END) as active_checkins,
                    COUNT(CASE WHEN status = 'Завершено' THEN 1 END) as completed_checkins,
                    AVG(CASE 
                        WHEN check_out_date IS NOT NULL 
                        THEN check_out_date - check_in_date 
                        ELSE CURRENT_DATE - check_in_date 
                    END) as avg_stay_duration
                FROM check_ins ci
                WHERE 1=1 {date_where}
            """, tuple(date_params))
            stats = db.fetchone()
            
            return {
                "total_checkins": stats['total_checkins'] or 0,
                "active_checkins": stats['active_checkins'] or 0,
                "completed_checkins": stats['completed_checkins'] or 0,
                "average_stay_duration": float(stats['avg_stay_duration'] or 0)
            }


checkin_service = CheckInService()