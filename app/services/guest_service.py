from typing import List, Optional
from datetime import datetime, date
from app.models.guest import Guest, GuestCreate, GuestUpdate, GuestSearchResult, GuestWithRoom
from app.db.database import DBSession


class GuestService:
    @classmethod
    def create(cls, guest_data: GuestCreate) -> Guest:
        with DBSession() as db:
            existing_guest = cls.get_by_passport(guest_data.passport_number)
            if existing_guest:
                raise ValueError(f"Постоялец с паспортом {guest_data.passport_number} уже существует")

            db.execute(
                """
                INSERT INTO guests (passport_number, last_name, first_name, middle_name, 
                                  birth_year, gender, registration_address, phone, 
                                  purpose_of_visit, how_heard_about_us)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    guest_data.passport_number, guest_data.last_name, guest_data.first_name,
                    guest_data.middle_name, guest_data.birth_year, guest_data.gender,
                    guest_data.registration_address, guest_data.phone,
                    guest_data.purpose_of_visit, guest_data.how_heard_about_us
                )
            )
            result = db.fetchone()
            return Guest(**result)

    @classmethod
    def get_by_id(cls, guest_id: int) -> Optional[Guest]:
        with DBSession() as db:
            db.execute("SELECT * FROM guests WHERE id = %s", (guest_id,))
            result = db.fetchone()
            return Guest(**result) if result else None

    @classmethod
    def get_by_passport(cls, passport_number: str) -> Optional[Guest]:
        with DBSession() as db:
            db.execute("SELECT * FROM view_guest_by_passport WHERE passport_number = %s", (passport_number,))
            result = db.fetchone()
            if result:
                return GuestWithRoom(**result)
            return None

    @classmethod
    def search_by_name(cls, last_name: Optional[str] = None, first_name: Optional[str] = None, middle_name: Optional[str] = None) -> List[GuestSearchResult]:
        """
        Поиск постояльца по ФИО.
        Результаты поиска: ФИО, Серия и номер паспорта.
        """
        with DBSession() as db:
            conditions = []
            params = []
            
            if last_name:
                conditions.append("LOWER(last_name) LIKE LOWER(%s)")
                params.append(f"%{last_name}%")
            
            if first_name:
                conditions.append("LOWER(first_name) LIKE LOWER(%s)")
                params.append(f"%{first_name}%")
                
            if middle_name:
                conditions.append("LOWER(middle_name) LIKE LOWER(%s)")
                params.append(f"%{middle_name}%")
            
            if not conditions:
                return []
            
            query = f"""
                SELECT id, last_name, first_name, middle_name, passport_number,
                       room_number, check_in_date, check_out_date
                FROM view_guest_by_name 
                WHERE {' AND '.join(conditions)}
                ORDER BY last_name, first_name
            """
            
            db.execute(query, tuple(params))
            results = db.fetchall()
            return [GuestSearchResult(**row) for row in results]

    @classmethod
    def get_all(cls, skip: int = 0, limit: int = 100) -> List[Guest]:
        """Получение списка всех зарегистрированных постояльцев."""
        with DBSession() as db:
            db.execute(
                "SELECT * FROM guests ORDER BY created_at DESC LIMIT %s OFFSET %s", 
                (limit, skip)
            )
            results = db.fetchall()
            return [Guest(**row) for row in results]

    @classmethod
    def get_current_guests(cls) -> List[GuestWithRoom]:
        """Получение списка текущих постояльцев в отеле."""
        with DBSession() as db:
            db.execute("SELECT * FROM view_current_guests ORDER BY room_number")
            results = db.fetchall()
            return [GuestWithRoom(**row) for row in results]

    @classmethod
    def filter_guests(
        cls, 
        room_number: Optional[str] = None,
        check_in_date: Optional[date] = None,
        passport_number: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GuestSearchResult]:
        """
        Фильтрация данных о постояльцах по:
        - № гостиничного номера
        - Дате поселения  
        - Паспортным данным
        """
        with DBSession() as db:
            conditions = []
            params = []
            
            if room_number:
                conditions.append("room_number = %s")
                params.append(room_number)
            
            if check_in_date:
                conditions.append("check_in_date = %s")
                params.append(check_in_date)
                
            if passport_number:
                conditions.append("passport_number LIKE %s")
                params.append(f"%{passport_number}%")
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT id, passport_number, last_name, first_name, middle_name, 
                       phone, room_number, booking_status, check_in_date, check_out_date
                FROM view_guest_search 
                {where_clause}
                ORDER BY check_in_date DESC, last_name
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, skip])
            db.execute(query, tuple(params))
            results = db.fetchall()
            return [GuestSearchResult(**row) for row in results]

    @classmethod
    def update(cls, guest_id: int, guest_data: GuestUpdate) -> Optional[Guest]:
        """Обновление данных постояльца."""
        if not any(v is not None for v in guest_data.dict().values()):
            return None
            
        with DBSession() as db:
            db.execute("SELECT id FROM guests WHERE id = %s", (guest_id,))
            if not db.fetchone():
                return None
                
            if guest_data.passport_number:
                db.execute("SELECT id FROM guests WHERE passport_number = %s AND id != %s", 
                          (guest_data.passport_number, guest_id))
                if db.fetchone():
                    raise ValueError(f"Постоялец с паспортом {guest_data.passport_number} уже существует")
                
            set_parts = []
            values = []

            update_dict = guest_data.dict(exclude_unset=True, exclude_none=True)
            for key, value in update_dict.items():
                set_parts.append(f"{key} = %s")
                values.append(value)
            
            if not set_parts:
                return None
                
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
                
            query = f"""
                UPDATE guests 
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
            """
            values.append(guest_id)
            
            db.execute(query, tuple(values))
            result = db.fetchone()
            return Guest(**result) if result else None

    @classmethod
    def delete(cls, guest_id: int) -> bool:
        """
        Удаление данных о постояльце.
        """
        with DBSession() as db:
            db.execute(
                "SELECT id FROM check_ins WHERE guest_id = %s AND status = 'Активно'", 
                (guest_id,)
            )
            if db.fetchone():
                raise ValueError("Нельзя удалить постояльца с активным заселением")
            
            db.execute("DELETE FROM guests WHERE id = %s", (guest_id,))
            return db.rowcount > 0

    @classmethod
    def get_guest_statistics(cls) -> dict:
        """Получение статистики по постояльцам."""
        with DBSession() as db:
            db.execute("SELECT COUNT(*) as total FROM guests")
            total_guests = db.fetchone()['total']
            
            db.execute("SELECT COUNT(*) as current FROM view_current_guests")
            current_guests = db.fetchone()['current']
            
            db.execute("""
                SELECT how_heard_about_us, COUNT(*) as count 
                FROM guests 
                WHERE how_heard_about_us IS NOT NULL 
                GROUP BY how_heard_about_us 
                ORDER BY count DESC
            """)
            sources = db.fetchall()
            
            return {
                "total_guests": total_guests,
                "current_guests": current_guests,
                "available_rooms": 0, 
                "guest_sources": [dict(row) for row in sources]
            }


guest_service = GuestService()