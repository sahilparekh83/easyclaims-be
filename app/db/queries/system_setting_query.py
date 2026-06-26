from typing import Optional
from ..session import session_scope
from ..models.system_setting import SystemSetting


class SystemSettingQuery:
    def get(self, key: str) -> Optional[str]:
        with session_scope() as session:
            row = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            return row.value if row else None

    def set(self, key: str, value: str, description: str = None) -> SystemSetting:
        with session_scope() as session:
            row = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            if row:
                row.value = value
                if description is not None:
                    row.description = description
            else:
                row = SystemSetting(key=key, value=value, description=description)
                session.add(row)
            session.flush()
            session.refresh(row)
            session.expunge(row)
            return row

    def list_all(self) -> list[SystemSetting]:
        with session_scope() as session:
            rows = session.query(SystemSetting).order_by(SystemSetting.key).all()
            for r in rows:
                session.expunge(r)
            return rows
