from app.db.database import DBSession

def safe_db_execute(query: str, params: tuple):
    with DBSession() as db:
        if db is None:
            raise Exception("Подключение к базе данных не установлено")
        if params:
            db.execute(query, params)
        else:
            db.execute(query)
        return db


def get_db_cursor():
    with DBSession() as db:
        if db is None:
            raise Exception("Подключение к базе данных не установлено")
        return db