from ..session import session_scope


class GenericRepository:
    def create_or_update(self, data: dict, table_class, filter_fields: dict):
        valid_columns = {c.key for c in table_class.__table__.columns}
        filtered = {k: v for k, v in data.items() if k in valid_columns}
        with session_scope() as session:
            obj = session.query(table_class).filter_by(**filter_fields).first()
            if obj:
                for key, value in filtered.items():
                    setattr(obj, key, value)
                session.add(obj)
                return obj
            obj = table_class(**filtered)
            session.add(obj)
            session.flush()
            return obj
