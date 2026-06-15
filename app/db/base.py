from sqlalchemy.orm import as_declarative, declared_attr


@as_declarative()
class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    def _asdict(self):
        from sqlalchemy import inspect
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
