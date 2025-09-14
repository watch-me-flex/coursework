from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.room import Room, RoomCreate, RoomUpdate, RoomType, RoomWithType, RoomAvailability
from app.db.database import DBSession


class RoomService:
    
    @classmethod
    def create_room_type(cls, code: str, name: str, description: str = None) -> RoomType:
        with DBSession() as db:
            db.execute("SELECT id FROM room_types WHERE code = %s", (code.upper(),))
            if db.fetchone():
                raise ValueError(f"Тип номера с кодом {code} уже существует")
                
            db.execute(
                "INSERT INTO room_types (code, name, description) VALUES (%s, %s, %s) RETURNING *",
                (code.upper(), name, description)
            )
            result = db.fetchone()
            return RoomType(**result)

    @classmethod
    def get_room_types(cls) -> List[RoomType]:
        with DBSession() as db:
            db.execute("SELECT * FROM room_types ORDER BY code")
            results = db.fetchall()
            return [RoomType(**row) for row in results]

    @classmethod
    def create_room(cls, room_data: RoomCreate) -> Room:
        with DBSession() as db:
            existing_room = cls.get_by_number(room_data.room_number)
            if existing_room:
                raise ValueError(f"Номер {room_data.room_number} уже существует")

            db.execute("SELECT id FROM room_types WHERE id = %s", (room_data.type_id,))
            if not db.fetchone():
                raise ValueError(f"Тип номера с ID {room_data.type_id} не существует")

            db.execute(
                """
                INSERT INTO rooms (room_number, type_id, capacity, room_count, 
                                 price_per_night, has_bathroom, equipment, is_available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    room_data.room_number, room_data.type_id, room_data.capacity,
                    room_data.room_count, room_data.price_per_night, room_data.has_bathroom,
                    room_data.equipment, room_data.is_available
                )
            )
            result = db.fetchone()
            return Room(**result)

    @classmethod
    def get_by_id(cls, room_id: int) -> Optional[Room]:
        with DBSession() as db:
            db.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
            result = db.fetchone()
            return Room(**result) if result else None

    @classmethod
    def get_by_number(cls, room_number: str) -> Optional[Room]:
        with DBSession() as db:
            db.execute("SELECT * FROM rooms WHERE room_number = %s", (room_number,))
            result = db.fetchone()
            return Room(**result) if result else None

    @classmethod
    def get_all(cls, skip: int = 0, limit: int = 100) -> List[RoomWithType]:
        with DBSession() as db:
            db.execute(
                """
                SELECT r.*, rt.code as type_code, rt.name as type_name, rt.description as type_description
                FROM rooms r
                LEFT JOIN room_types rt ON r.type_id = rt.id
                ORDER BY r.room_number
                LIMIT %s OFFSET %s
                """,
                (limit, skip)
            )
            results = db.fetchall()
            return [RoomWithType(**row) for row in results]

    @classmethod
    def get_available_rooms(cls, check_in_date: date = None, check_out_date: date = None) -> List[RoomAvailability]:
        with DBSession() as db:
            if check_in_date and check_out_date:
                query = """
                    SELECT r.id as room_id, r.room_number, rt.name as type_name, 
                           r.capacity, r.price_per_night, r.is_available,
                           COALESCE(current_guests.guest_count, 0) as current_guest_count
                    FROM rooms r
                    LEFT JOIN room_types rt ON r.type_id = rt.id
                    LEFT JOIN (
                        SELECT room_id, COUNT(*) as guest_count
                        FROM check_ins ci
                        WHERE ci.status = 'Активно'
                        AND ci.check_in_date <= %s
                        AND (ci.check_out_date IS NULL OR ci.check_out_date >= %s)
                        GROUP BY room_id
                    ) current_guests ON r.id = current_guests.room_id
                    WHERE r.is_available = true
                    AND r.id NOT IN (
                        SELECT DISTINCT room_id
                        FROM check_ins ci
                        WHERE ci.status = 'Активно'
                        AND ci.check_in_date < %s
                        AND (ci.check_out_date IS NULL OR ci.check_out_date > %s)
                    )
                    ORDER BY r.room_number
                """
                db.execute(query, (check_out_date, check_in_date, check_out_date, check_in_date))
            else:
                query = """
                    SELECT r.id as room_id, r.room_number, rt.name as type_name, 
                           r.capacity, r.price_per_night, r.is_available,
                           COALESCE(current_guests.guest_count, 0) as current_guest_count
                    FROM rooms r
                    LEFT JOIN room_types rt ON r.type_id = rt.id
                    LEFT JOIN (
                        SELECT room_id, COUNT(*) as guest_count
                        FROM check_ins ci
                        WHERE ci.status = 'Активно'
                        GROUP BY room_id
                    ) current_guests ON r.id = current_guests.room_id
                    WHERE r.is_available = true
                    ORDER BY r.room_number
                """
                db.execute(query)
            
            results = db.fetchall()
            return [RoomAvailability(**row) for row in results]

    @classmethod
    def update(cls, room_id: int, room_data: RoomUpdate) -> Optional[Room]:
        if not any(v is not None for v in room_data.dict().values()):
            return None
            
        with DBSession() as db:
            db.execute("SELECT id FROM rooms WHERE id = %s", (room_id,))
            if not db.fetchone():
                return None
                
            if room_data.room_number:
                db.execute("SELECT id FROM rooms WHERE room_number = %s AND id != %s", 
                          (room_data.room_number, room_id))
                if db.fetchone():
                    raise ValueError(f"Номер {room_data.room_number} уже существует")
                
            set_parts = []
            values = []

            update_dict = room_data.dict(exclude_unset=True, exclude_none=True)
            for key, value in update_dict.items():
                set_parts.append(f"{key} = %s")
                values.append(value)
            
            if not set_parts:
                return None
                
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
                
            query = f"""
                UPDATE rooms 
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
            """
            values.append(room_id)
            
            db.execute(query, tuple(values))
            result = db.fetchone()
            return Room(**result) if result else None

    @classmethod
    def delete(cls, room_id: int) -> bool:
        with DBSession() as db:
            db.execute(
                "SELECT id FROM check_ins WHERE room_id = %s AND status = 'Активно'", 
                (room_id,)
            )
            if db.fetchone():
                raise ValueError("Нельзя удалить номер с активными заселениями")
            
            db.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
            return db.rowcount > 0

    @classmethod
    def set_availability(cls, room_id: int, is_available: bool) -> Optional[Room]:
        with DBSession() as db:
            db.execute(
                """
                UPDATE rooms 
                SET is_available = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *
                """,
                (is_available, room_id)
            )
            result = db.fetchone()
            return Room(**result) if result else None

    @classmethod
    def get_room_statistics(cls) -> dict:
        with DBSession() as db:
            db.execute("""
                SELECT 
                    COUNT(*) as total_rooms,
                    SUM(capacity) as total_capacity,
                    COUNT(CASE WHEN is_available = false THEN 1 END) as rooms_on_maintenance,
                    COUNT(CASE WHEN is_available = true THEN 1 END) as available_rooms,
                    SUM(CASE WHEN is_available = true THEN capacity END) as available_capacity
                FROM rooms
            """)
            stats = db.fetchone()
            
            db.execute("""
                SELECT 
                    COUNT(DISTINCT ci.room_id) as occupied_rooms,
                    COUNT(ci.id) as occupied_capacity
                FROM check_ins ci
                WHERE ci.status = 'Активно'
            """)
            occupancy = db.fetchone()
            
            db.execute("""
                SELECT rt.name, rt.code, COUNT(r.id) as count, 
                       AVG(r.price_per_night) as avg_price
                FROM room_types rt
                LEFT JOIN rooms r ON rt.id = r.type_id
                GROUP BY rt.id, rt.name, rt.code
                ORDER BY rt.code
            """)
            types_stats = db.fetchall()
            
            total_rooms = stats['total_rooms'] or 0
            available_rooms = stats['available_rooms'] or 0
            occupied_rooms = occupancy['occupied_rooms'] or 0
            
            room_occupancy_percent = (occupied_rooms / available_rooms * 100) if available_rooms > 0 else 0
            capacity_occupancy_percent = (
                (occupancy['occupied_capacity'] or 0) / (stats['available_capacity'] or 1) * 100
            ) if stats['available_capacity'] else 0
            
            return {
                "total_rooms": total_rooms,
                "total_capacity": stats['total_capacity'] or 0,
                "rooms_on_maintenance": stats['rooms_on_maintenance'] or 0,
                "available_rooms": available_rooms,
                "available_capacity": stats['available_capacity'] or 0,
                "occupied_rooms": occupied_rooms,
                "occupied_capacity": occupancy['occupied_capacity'] or 0,
                "room_occupancy_percent": round(room_occupancy_percent, 2),
                "capacity_occupancy_percent": round(capacity_occupancy_percent, 2),
                "types_statistics": [dict(row) for row in types_stats]
            }


room_service = RoomService()