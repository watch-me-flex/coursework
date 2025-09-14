from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.models.service import (
    Service, ServiceCreate, ServiceUpdate, ServiceWithType,
    ServiceType, ServiceTypeCreate, ServiceTypeUpdate,
    ServiceUsageStats, ServiceRevenueReport
)
from app.db.database import DBSession


class ServiceService:
    @classmethod
    def create_service_type(cls, service_type_data: ServiceTypeCreate) -> ServiceType:
        with DBSession() as db:
            db.execute("SELECT id FROM service_types WHERE name = %s", (service_type_data.name,))
            if db.fetchone():
                raise ValueError(f"Тип услуги '{service_type_data.name}' уже существует")
                
            db.execute(
                "INSERT INTO service_types (name, description) VALUES (%s, %s) RETURNING *",
                (service_type_data.name, service_type_data.description)
            )
            result = db.fetchone()
            return ServiceType(**result)

    @classmethod
    def get_service_types(cls) -> List[ServiceType]:
        with DBSession() as db:
            db.execute("SELECT * FROM service_types ORDER BY name")
            results = db.fetchall()
            return [ServiceType(**row) for row in results]

    @classmethod
    def update_service_type(cls, type_id: int, service_type_data: ServiceTypeUpdate) -> Optional[ServiceType]:
        if not any(v is not None for v in service_type_data.dict().values()):
            return None
            
        with DBSession() as db:
            db.execute("SELECT id FROM service_types WHERE id = %s", (type_id,))
            if not db.fetchone():
                return None
                
            set_parts = []
            values = []

            update_dict = service_type_data.dict(exclude_unset=True, exclude_none=True)
            for key, value in update_dict.items():
                set_parts.append(f"{key} = %s")
                values.append(value)
            
            if not set_parts:
                return None
                
            query = f"""
                UPDATE service_types 
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
            """
            values.append(type_id)
            
            db.execute(query, tuple(values))
            result = db.fetchone()
            return ServiceType(**result) if result else None

    @classmethod
    def delete_service_type(cls, type_id: int) -> bool:
        with DBSession() as db:
            db.execute("SELECT id FROM services WHERE type_id = %s", (type_id,))
            if db.fetchone():
                raise ValueError("Нельзя удалить тип услуги, который используется")
            
            db.execute("DELETE FROM service_types WHERE id = %s", (type_id,))
            return db.rowcount > 0

    @classmethod
    def create_service(cls, service_data: ServiceCreate) -> Service:
        with DBSession() as db:
            db.execute("SELECT id FROM service_types WHERE id = %s", (service_data.type_id,))
            if not db.fetchone():
                raise ValueError(f"Тип услуги с ID {service_data.type_id} не существует")

            db.execute(
                "SELECT id FROM services WHERE name = %s AND type_id = %s", 
                (service_data.name, service_data.type_id)
            )
            if db.fetchone():
                raise ValueError(f"Услуга '{service_data.name}' уже существует в данном типе")

            db.execute(
                """
                INSERT INTO services (type_id, name, description, price, is_available)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    service_data.type_id, service_data.name, service_data.description,
                    service_data.price, service_data.is_available
                )
            )
            result = db.fetchone()
            return Service(**result)

    @classmethod
    def get_by_id(cls, service_id: int) -> Optional[Service]:
        with DBSession() as db:
            db.execute("SELECT * FROM services WHERE id = %s", (service_id,))
            result = db.fetchone()
            return Service(**result) if result else None

    @classmethod
    def get_service_with_type(cls, service_id: int) -> Optional[ServiceWithType]:
        with DBSession() as db:
            db.execute(
                """
                SELECT s.*, st.name as type_name, st.description as type_description
                FROM services s
                LEFT JOIN service_types st ON s.type_id = st.id
                WHERE s.id = %s
                """,
                (service_id,)
            )
            result = db.fetchone()
            return ServiceWithType(**result) if result else None

    @classmethod
    def get_all_services(
        cls, 
        type_id: int = None,
        is_available: bool = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ServiceWithType]:
        with DBSession() as db:
            conditions = []
            params = []
            
            if type_id:
                conditions.append("s.type_id = %s")
                params.append(type_id)
            
            if is_available is not None:
                conditions.append("s.is_available = %s")
                params.append(is_available)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT s.*, st.name as type_name, st.description as type_description
                FROM services s
                LEFT JOIN service_types st ON s.type_id = st.id
                {where_clause}
                ORDER BY st.name, s.name
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, skip])
            db.execute(query, tuple(params))
            results = db.fetchall()
            return [ServiceWithType(**row) for row in results]

    @classmethod
    def get_services_by_type(cls, type_name: str) -> List[ServiceWithType]:
        with DBSession() as db:
            db.execute(
                """
                SELECT s.*, st.name as type_name, st.description as type_description
                FROM services s
                JOIN service_types st ON s.type_id = st.id
                WHERE LOWER(st.name) LIKE LOWER(%s) AND s.is_available = true
                ORDER BY s.name
                """,
                (f"%{type_name}%",)
            )
            results = db.fetchall()
            return [ServiceWithType(**row) for row in results]

    @classmethod
    def update(cls, service_id: int, service_data: ServiceUpdate) -> Optional[Service]:
        if not any(v is not None for v in service_data.dict().values()):
            return None
            
        with DBSession() as db:
            db.execute("SELECT id FROM services WHERE id = %s", (service_id,))
            if not db.fetchone():
                return None
                
            set_parts = []
            values = []

            update_dict = service_data.dict(exclude_unset=True, exclude_none=True)
            for key, value in update_dict.items():
                set_parts.append(f"{key} = %s")
                values.append(value)
            
            if not set_parts:
                return None
                
            query = f"""
                UPDATE services 
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
            """
            values.append(service_id)
            
            db.execute(query, tuple(values))
            result = db.fetchone()
            return Service(**result) if result else None

    @classmethod
    def delete(cls, service_id: int) -> bool:
        with DBSession() as db:
            db.execute("SELECT id FROM service_payments WHERE service_id = %s", (service_id,))
            if db.fetchone():
                raise ValueError("Нельзя удалить услугу, за которую есть платежи")
            
            db.execute("DELETE FROM services WHERE id = %s", (service_id,))
            return db.rowcount > 0

    @classmethod
    def set_availability(cls, service_id: int, is_available: bool) -> Optional[Service]:
        with DBSession() as db:
            db.execute(
                "UPDATE services SET is_available = %s WHERE id = %s RETURNING *",
                (is_available, service_id)
            )
            result = db.fetchone()
            return Service(**result) if result else None

    @classmethod
    def get_service_usage_stats(
        cls, 
        date_from: date = None, 
        date_to: date = None
    ) -> List[ServiceUsageStats]:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("DATE(sp.payment_date) >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("DATE(sp.payment_date) <= %s")
                date_params.append(date_to)
            
            date_where = "AND " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT 
                    s.id as service_id,
                    s.name as service_name,
                    st.name as service_type,
                    COALESCE(SUM(sp.amount), 0) as total_revenue,
                    COUNT(sp.id) as usage_count,
                    COALESCE(AVG(sp.amount), 0) as average_order_value
                FROM services s
                LEFT JOIN service_payments sp ON s.id = sp.service_id AND sp.status = 'Оплачено'
                LEFT JOIN service_types st ON s.type_id = st.id
                WHERE 1=1 {date_where}
                GROUP BY s.id, s.name, st.name
                ORDER BY total_revenue DESC
            """, tuple(date_params))
            
            results = db.fetchall()
            return [ServiceUsageStats(**row) for row in results]

    @classmethod
    def get_service_revenue_report(
        cls, 
        date_from: date = None, 
        date_to: date = None
    ) -> List[ServiceRevenueReport]:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("DATE(sp.payment_date) >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("DATE(sp.payment_date) <= %s")
                date_params.append(date_to)
            
            date_where = "AND " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT COALESCE(SUM(amount), 0) as total_revenue
                FROM service_payments
                WHERE status = 'Оплачено' {date_where}
            """, tuple(date_params))
            total_revenue = db.fetchone()['total_revenue'] or 0
            
            db.execute(f"""
                SELECT 
                    st.name as service_type,
                    COALESCE(SUM(sp.amount), 0) as total_revenue,
                    COUNT(sp.id) as orders_count,
                    CASE 
                        WHEN %s > 0 THEN (COALESCE(SUM(sp.amount), 0) * 100.0 / %s)
                        ELSE 0 
                    END as percentage_of_total
                FROM service_types st
                LEFT JOIN services s ON st.id = s.type_id
                LEFT JOIN service_payments sp ON s.id = sp.service_id AND sp.status = 'Оплачено'
                WHERE 1=1 {date_where}
                GROUP BY st.id, st.name
                ORDER BY total_revenue DESC
            """, [total_revenue, total_revenue] + date_params)
            
            results = db.fetchall()
            return [ServiceRevenueReport(**row) for row in results]

    @classmethod
    def get_popular_services(cls, limit: int = 10) -> List[dict]:
        with DBSession() as db:
            db.execute("""
                SELECT 
                    s.name,
                    st.name as service_type,
                    COUNT(sp.id) as usage_count,
                    SUM(sp.amount) as total_revenue
                FROM services s
                JOIN service_types st ON s.type_id = st.id
                LEFT JOIN service_payments sp ON s.id = sp.service_id AND sp.status = 'Оплачено'
                GROUP BY s.id, s.name, st.name
                ORDER BY usage_count DESC, total_revenue DESC
                LIMIT %s
            """, (limit,))
            
            results = db.fetchall()
            return [dict(row) for row in results]


service_service = ServiceService()