from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.models.action_log import (
    ActionLog, ActionLogCreate, ActionLogWithUser, 
    ActionLogFilter, ActionLogSummary, ActionType
)
from app.db.database import DBSession


class ActionLogService:
    
    @classmethod
    def create_log(
        cls, 
        user_id: Optional[int],
        action_type: ActionType,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> ActionLog:
        with DBSession() as db:
            log_data = ActionLogCreate(
                user_id=user_id,
                action_type=action_type,
                table_name=table_name,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values
            )
            
            db.execute(
                """
                INSERT INTO action_logs (user_id, action_type, table_name, record_id, old_values, new_values)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    log_data.user_id, log_data.action_type.value, log_data.table_name,
                    log_data.record_id, log_data.old_values, log_data.new_values
                )
            )
            result = db.fetchone()
            return ActionLog(**result)
    
    @classmethod
    def get_logs_with_filters(cls, filters: ActionLogFilter) -> List[ActionLogWithUser]:
        with DBSession() as db:
            conditions = []
            params = []
            
            if filters.user_id:
                conditions.append("al.user_id = %s")
                params.append(filters.user_id)
            
            if filters.username:
                conditions.append("LOWER(u.username) LIKE LOWER(%s)")
                params.append(f"%{filters.username}%")
            
            if filters.action_type:
                conditions.append("al.action_type = %s")
                params.append(filters.action_type.value)
            
            if filters.table_name:
                conditions.append("al.table_name = %s")
                params.append(filters.table_name)
            
            if filters.date_from:
                conditions.append("DATE(al.created_at) >= %s")
                params.append(filters.date_from)
            
            if filters.date_to:
                conditions.append("DATE(al.created_at) <= %s")
                params.append(filters.date_to)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT 
                    al.*,
                    u.username,
                    u.full_name as user_full_name,
                    r.name as user_role
                FROM action_logs al
                LEFT JOIN users u ON al.user_id = u.id
                LEFT JOIN roles r ON u.role_id = r.id
                {where_clause}
                ORDER BY al.created_at DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([filters.limit, filters.offset])
            db.execute(query, tuple(params))
            results = db.fetchall()
            
            return [ActionLogWithUser(**row) for row in results]
    
    @classmethod
    def get_user_actions_summary(
        cls, 
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[ActionLogSummary]:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("DATE(al.created_at) >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("DATE(al.created_at) <= %s")
                date_params.append(date_to)
            
            date_where = "AND " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.full_name as user_full_name,
                    COUNT(al.id) as total_actions,
                    MAX(al.created_at) as last_action_date
                FROM users u
                LEFT JOIN action_logs al ON u.id = al.user_id
                WHERE u.id IS NOT NULL {date_where}
                GROUP BY u.id, u.username, u.full_name
                HAVING COUNT(al.id) > 0
                ORDER BY total_actions DESC
            """, tuple(date_params))
            
            results = db.fetchall()
            summaries = []
            
            for row in results:
                db.execute(f"""
                    SELECT action_type, COUNT(*) as count
                    FROM action_logs
                    WHERE user_id = %s {date_where.replace('al.', '')}
                    GROUP BY action_type
                    ORDER BY count DESC
                """, [row['user_id']] + date_params)
                
                actions_by_type = {action_row['action_type']: action_row['count'] 
                                 for action_row in db.fetchall()}
                
                summaries.append(ActionLogSummary(
                    user_id=row['user_id'],
                    username=row['username'],
                    user_full_name=row['user_full_name'],
                    total_actions=row['total_actions'],
                    actions_by_type=actions_by_type,
                    last_action_date=row['last_action_date']
                ))
            
            return summaries
    
    @classmethod
    def get_system_activity_stats(
        cls,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        with DBSession() as db:
            date_conditions = []
            date_params = []
            
            if date_from:
                date_conditions.append("DATE(created_at) >= %s")
                date_params.append(date_from)
            
            if date_to:
                date_conditions.append("DATE(created_at) <= %s")
                date_params.append(date_to)
            
            date_where = "WHERE " + " AND ".join(date_conditions) if date_conditions else ""
            
            db.execute(f"""
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(DISTINCT table_name) as affected_tables,
                    MIN(created_at) as first_action,
                    MAX(created_at) as last_action
                FROM action_logs
                {date_where}
            """, tuple(date_params))
            
            general_stats = db.fetchone()
            
            db.execute(f"""
                SELECT action_type, COUNT(*) as count
                FROM action_logs
                {date_where}
                GROUP BY action_type
                ORDER BY count DESC
            """, tuple(date_params))
            
            actions_by_type = {row['action_type']: row['count'] for row in db.fetchall()}
            
            db.execute(f"""
                SELECT table_name, COUNT(*) as count
                FROM action_logs
                {date_where}
                GROUP BY table_name
                ORDER BY count DESC
            """, tuple(date_params))
            
            actions_by_table = {row['table_name']: row['count'] for row in db.fetchall()}
            
            db.execute(f"""
                SELECT 
                    DATE(created_at) as action_date,
                    COUNT(*) as daily_actions
                FROM action_logs
                {date_where}
                GROUP BY DATE(created_at)
                ORDER BY action_date DESC
                LIMIT 7
            """, tuple(date_params))
            
            daily_activity = [dict(row) for row in db.fetchall()]
            
            return {
                "total_actions": general_stats['total_actions'] or 0,
                "active_users": general_stats['active_users'] or 0,
                "affected_tables": general_stats['affected_tables'] or 0,
                "first_action": general_stats['first_action'],
                "last_action": general_stats['last_action'],
                "actions_by_type": actions_by_type,
                "actions_by_table": actions_by_table,
                "daily_activity": daily_activity
            }
    
    @classmethod
    def set_current_user_context(cls, user_id: int):
        with DBSession() as db:
            db.execute("SELECT set_config('app.current_user_id', %s, true)", (str(user_id),))
    
    @classmethod
    def clear_user_context(cls):
        with DBSession() as db:
            db.execute("SELECT set_config('app.current_user_id', '', true)")


action_log_service = ActionLogService()