from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.payment import (
    RoomPayment, RoomPaymentCreate, RoomPaymentUpdate, RoomPaymentWithDetails,
    ServicePayment, ServicePaymentCreate, ServicePaymentUpdate, ServicePaymentWithDetails,
    PaymentStatus, PaymentMethod, PaymentSummary
)
from app.db.database import DBSession


class PaymentService:    
    @classmethod
    def create_room_payment(cls, payment_data: RoomPaymentCreate) -> RoomPayment:
        with DBSession() as db:
            db.execute(
                """
                SELECT ci.*, r.room_number, r.price_per_night
                FROM check_ins ci
                JOIN rooms r ON ci.room_id = r.id
                WHERE ci.id = %s
                """,
                (payment_data.check_in_id,)
            )
            check_in_info = db.fetchone()
            if not check_in_info:
                raise ValueError(f"Заселение с ID {payment_data.check_in_id} не найдено")
            
            if payment_data.amount == 0:
                calculated_amount = check_in_info['price_per_night'] * payment_data.days_count
                payment_data.amount = calculated_amount
            
            db.execute(
                """
                INSERT INTO room_payments (check_in_id, days_count, amount, payment_method, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payment_data.check_in_id, payment_data.days_count, payment_data.amount,
                    payment_data.payment_method.value, payment_data.status.value
                )
            )
            result = db.fetchone()
            return RoomPayment(**result)

    @classmethod
    def get_room_payment_by_id(cls, payment_id: int) -> Optional[RoomPayment]:
        with DBSession() as db:
            db.execute("SELECT * FROM room_payments WHERE id = %s", (payment_id,))
            result = db.fetchone()
            return RoomPayment(**result) if result else None

    @classmethod
    def get_room_payment_with_details(cls, payment_id: int) -> Optional[RoomPaymentWithDetails]:
        with DBSession() as db:
            db.execute(
                """
                SELECT rp.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       r.room_number,
                       ci.check_in_date,
                       ci.check_out_date
                FROM room_payments rp
                JOIN check_ins ci ON rp.check_in_id = ci.id
                JOIN guests g ON ci.guest_id = g.id
                JOIN rooms r ON ci.room_id = r.id
                WHERE rp.id = %s
                """,
                (payment_id,)
            )
            result = db.fetchone()
            return RoomPaymentWithDetails(**result) if result else None

    @classmethod
    def get_room_payments_by_check_in(cls, check_in_id: int) -> List[RoomPayment]:
        with DBSession() as db:
            db.execute(
                "SELECT * FROM room_payments WHERE check_in_id = %s ORDER BY payment_date",
                (check_in_id,)
            )
            results = db.fetchall()
            return [RoomPayment(**row) for row in results]

    @classmethod
    def create_service_payment(cls, payment_data: ServicePaymentCreate) -> ServicePayment:
        with DBSession() as db:
            db.execute("SELECT id FROM guests WHERE id = %s", (payment_data.guest_id,))
            if not db.fetchone():
                raise ValueError(f"Гость с ID {payment_data.guest_id} не найден")
            
            db.execute("SELECT price FROM services WHERE id = %s", (payment_data.service_id,))
            service_info = db.fetchone()
            if not service_info:
                raise ValueError(f"Услуга с ID {payment_data.service_id} не найдена")
            
            if payment_data.amount == 0:
                calculated_amount = service_info['price'] * payment_data.quantity
                payment_data.amount = calculated_amount
            
            db.execute(
                """
                INSERT INTO service_payments (guest_id, service_id, amount, quantity, payment_method, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payment_data.guest_id, payment_data.service_id, payment_data.amount,
                    payment_data.quantity, payment_data.payment_method.value, payment_data.status.value
                )
            )
            result = db.fetchone()
            return ServicePayment(**result)

    @classmethod
    def get_service_payment_by_id(cls, payment_id: int) -> Optional[ServicePayment]:
        with DBSession() as db:
            db.execute("SELECT * FROM service_payments WHERE id = %s", (payment_id,))
            result = db.fetchone()
            return ServicePayment(**result) if result else None

    @classmethod
    def get_service_payment_with_details(cls, payment_id: int) -> Optional[ServicePaymentWithDetails]:
        with DBSession() as db:
            db.execute(
                """
                SELECT sp.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       s.name as service_name,
                       st.name as service_type
                FROM service_payments sp
                JOIN guests g ON sp.guest_id = g.id
                JOIN services s ON sp.service_id = s.id
                JOIN service_types st ON s.type_id = st.id
                WHERE sp.id = %s
                """,
                (payment_id,)
            )
            result = db.fetchone()
            return ServicePaymentWithDetails(**result) if result else None

    @classmethod
    def get_service_payments_by_guest(cls, guest_id: int) -> List[ServicePayment]:
        with DBSession() as db:
            db.execute(
                "SELECT * FROM service_payments WHERE guest_id = %s ORDER BY payment_date",
                (guest_id,)
            )
            results = db.fetchall()
            return [ServicePayment(**row) for row in results]

    @classmethod
    def update_room_payment_status(cls, payment_id: int, status: PaymentStatus) -> Optional[RoomPayment]:
        with DBSession() as db:
            db.execute(
                "UPDATE room_payments SET status = %s WHERE id = %s RETURNING *",
                (status.value, payment_id)
            )
            result = db.fetchone()
            return RoomPayment(**result) if result else None

    @classmethod
    def update_service_payment_status(cls, payment_id: int, status: PaymentStatus) -> Optional[ServicePayment]:
        with DBSession() as db:
            db.execute(
                "UPDATE service_payments SET status = %s WHERE id = %s RETURNING *",
                (status.value, payment_id)
            )
            result = db.fetchone()
            return ServicePayment(**result) if result else None

    @classmethod
    def get_all_room_payments(
        cls, 
        status: PaymentStatus = None,
        date_from: date = None,
        date_to: date = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RoomPaymentWithDetails]:
        with DBSession() as db:
            conditions = []
            params = []
            
            if status:
                conditions.append("rp.status = %s")
                params.append(status.value)
            
            if date_from:
                conditions.append("DATE(rp.payment_date) >= %s")
                params.append(date_from)
                
            if date_to:
                conditions.append("DATE(rp.payment_date) <= %s")
                params.append(date_to)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT rp.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       r.room_number,
                       ci.check_in_date,
                       ci.check_out_date
                FROM room_payments rp
                JOIN check_ins ci ON rp.check_in_id = ci.id
                JOIN guests g ON ci.guest_id = g.id
                JOIN rooms r ON ci.room_id = r.id
                {where_clause}
                ORDER BY rp.payment_date DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, skip])
            db.execute(query, tuple(params))
            results = db.fetchall()
            return [RoomPaymentWithDetails(**row) for row in results]

    @classmethod
    def get_all_service_payments(
        cls, 
        status: PaymentStatus = None,
        date_from: date = None,
        date_to: date = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ServicePaymentWithDetails]:
        with DBSession() as db:
            conditions = []
            params = []
            
            if status:
                conditions.append("sp.status = %s")
                params.append(status.value)
            
            if date_from:
                conditions.append("DATE(sp.payment_date) >= %s")
                params.append(date_from)
                
            if date_to:
                conditions.append("DATE(sp.payment_date) <= %s")
                params.append(date_to)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT sp.*, 
                       g.passport_number as guest_passport,
                       CONCAT(g.last_name, ' ', g.first_name, ' ', g.middle_name) as guest_full_name,
                       s.name as service_name,
                       st.name as service_type
                FROM service_payments sp
                JOIN guests g ON sp.guest_id = g.id
                JOIN services s ON sp.service_id = s.id
                JOIN service_types st ON s.type_id = st.id
                {where_clause}
                ORDER BY sp.payment_date DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, skip])
            db.execute(query, tuple(params))
            results = db.fetchall()
            return [ServicePaymentWithDetails(**row) for row in results]

    @classmethod
    def get_payment_summary(
        cls, 
        date_from: date = None, 
        date_to: date = None
    ) -> PaymentSummary:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("DATE(payment_date) >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("DATE(payment_date) <= %s")
                date_params.append(date_to)
            
            date_where = "WHERE " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT 
                    COALESCE(SUM(amount), 0) as total_revenue,
                    COUNT(*) as payments_count,
                    COALESCE(AVG(amount), 0) as avg_payment
                FROM room_payments
                {date_where} AND status = 'Оплачено'
            """, tuple(date_params))
            room_stats = db.fetchone()
            
            db.execute(f"""
                SELECT 
                    COALESCE(SUM(amount), 0) as total_revenue,
                    COUNT(*) as payments_count,
                    COALESCE(AVG(amount), 0) as avg_payment
                FROM service_payments
                {date_where} AND status = 'Оплачено'
            """, tuple(date_params))
            service_stats = db.fetchone()
            
            total_room_revenue = Decimal(str(room_stats['total_revenue']))
            total_service_revenue = Decimal(str(service_stats['total_revenue']))
            
            return PaymentSummary(
                total_room_revenue=total_room_revenue,
                total_service_revenue=total_service_revenue,
                total_revenue=total_room_revenue + total_service_revenue,
                room_payments_count=room_stats['payments_count'],
                service_payments_count=service_stats['payments_count'],
                average_room_payment=Decimal(str(room_stats['avg_payment'])),
                average_service_payment=Decimal(str(service_stats['avg_payment']))
            )

    @classmethod
    def get_revenue_by_room(
        cls, 
        date_from: date = None, 
        date_to: date = None
    ) -> List[dict]:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("DATE(rp.payment_date) >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("DATE(rp.payment_date) <= %s")
                date_params.append(date_to)
            
            date_where = "AND " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT 
                    r.room_number,
                    rt.name as room_type,
                    COALESCE(SUM(rp.amount), 0) as total_revenue,
                    COUNT(rp.id) as payments_count,
                    COALESCE(AVG(rp.amount), 0) as avg_payment,
                    SUM(rp.days_count) as total_days_sold
                FROM rooms r
                LEFT JOIN check_ins ci ON r.id = ci.room_id
                LEFT JOIN room_payments rp ON ci.id = rp.check_in_id AND rp.status = 'Оплачено'
                LEFT JOIN room_types rt ON r.type_id = rt.id
                WHERE 1=1 {date_where}
                GROUP BY r.id, r.room_number, rt.name
                ORDER BY total_revenue DESC
            """, tuple(date_params))
            
            results = db.fetchall()
            return [dict(row) for row in results]


payment_service = PaymentService()