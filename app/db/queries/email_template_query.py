from typing import Optional, List
from ..models.email_template import EmailTemplate
from ..session import session_scope


class EmailTemplateQuery:
    def get_by_slug(self, slug: str) -> Optional[EmailTemplate]:
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.slug == slug,
                EmailTemplate.is_active == True,
            ).first()
            if t:
                session.expunge(t)
            return t

    def get_by_id(self, template_id: str) -> Optional[EmailTemplate]:
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.id == _uuid.UUID(str(template_id))
            ).first()
            if t:
                session.expunge(t)
            return t

    def list_all(self) -> List[EmailTemplate]:
        with session_scope() as session:
            rows = session.query(EmailTemplate).order_by(EmailTemplate.slug).all()
            for r in rows:
                session.expunge(r)
            return rows

    def upsert(self, slug: str, subject: str, html_body: str, description: str = "") -> EmailTemplate:
        """Insert or update by slug. Used by seeder."""
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(EmailTemplate.slug == slug).first()
            if t:
                t.subject = subject
                t.html_body = html_body
                if description:
                    t.description = description
                session.flush()
                session.expunge(t)
                return t
            t = EmailTemplate(slug=slug, subject=subject, html_body=html_body, description=description)
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def create_if_not_exists(self, slug: str, html_body: str, subject: str = None,
                             description: str = "", channel_type: str = "email") -> EmailTemplate:
        """Insert only if slug doesn't already exist. Preserves admin-edited content on restarts."""
        with session_scope() as session:
            existing = session.query(EmailTemplate).filter(EmailTemplate.slug == slug).first()
            if existing:
                session.expunge(existing)
                return existing
            t = EmailTemplate(slug=slug, subject=subject, html_body=html_body,
                              description=description, channel_type=channel_type)
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def update(self, template_id: str, **kwargs) -> Optional[EmailTemplate]:
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.id == _uuid.UUID(str(template_id))
            ).first()
            if not t:
                return None
            for k, v in kwargs.items():
                setattr(t, k, v)
            session.flush()
            session.expunge(t)
            return t
