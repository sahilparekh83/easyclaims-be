from typing import Optional, List
from ..models.email_template import EmailTemplate
from ..session import session_scope


class EmailTemplateQuery:
    def get_by_slug(self, slug: str, channel_type: str = "email") -> Optional[EmailTemplate]:
        """System default template for this slug (partner_id IS NULL)."""
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.slug == slug,
                EmailTemplate.channel_type == channel_type,
                EmailTemplate.partner_id.is_(None),
                EmailTemplate.is_active == True,
            ).first()
            if t:
                session.expunge(t)
            return t

    def get_for_partner(self, slug: str, partner_id: Optional[str], channel_type: str = "email") -> Optional[EmailTemplate]:
        """Partner-specific override if one is set and active, else the system default (E6)."""
        if partner_id:
            with session_scope() as session:
                t = session.query(EmailTemplate).filter(
                    EmailTemplate.slug == slug,
                    EmailTemplate.channel_type == channel_type,
                    EmailTemplate.partner_id == partner_id,
                    EmailTemplate.is_active == True,
                ).first()
                if t:
                    session.expunge(t)
                    return t
        return self.get_by_slug(slug, channel_type=channel_type)

    def list_overrides_for_slug(self, slug: str) -> List[EmailTemplate]:
        with session_scope() as session:
            rows = session.query(EmailTemplate).filter(
                EmailTemplate.slug == slug,
                EmailTemplate.partner_id.isnot(None),
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def create_override(self, slug: str, partner_id: str, subject: str,
                        html_body: str, description: str = "") -> EmailTemplate:
        with session_scope() as session:
            existing = session.query(EmailTemplate).filter(
                EmailTemplate.slug == slug, EmailTemplate.partner_id == partner_id,
            ).first()
            if existing:
                raise ValueError(f"An override for '{slug}' already exists for this partner")
            t = EmailTemplate(
                slug=slug, partner_id=partner_id, subject=subject,
                html_body=html_body, description=description,
            )
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def delete_override(self, template_id: str) -> bool:
        """Delete a partner override only — system default templates (partner_id NULL) cannot be deleted."""
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.id == _uuid.UUID(str(template_id)),
                EmailTemplate.partner_id.isnot(None),
            ).first()
            if not t:
                return False
            session.delete(t)
            return True

    def get_by_id(self, template_id: str) -> Optional[EmailTemplate]:
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.id == _uuid.UUID(str(template_id))
            ).first()
            if t:
                session.expunge(t)
            return t

    def list_all(self, partner_id: Optional[str] = None, channel_type: str = "email") -> List[EmailTemplate]:
        """By default lists only system-default email templates. Pass partner_id to also
        include that partner's overrides (used by the admin UI's per-partner view)."""
        with session_scope() as session:
            q = session.query(EmailTemplate).filter(EmailTemplate.channel_type == channel_type)
            if partner_id:
                q = q.filter(
                    (EmailTemplate.partner_id.is_(None)) | (EmailTemplate.partner_id == partner_id)
                )
            else:
                q = q.filter(EmailTemplate.partner_id.is_(None))
            rows = q.order_by(EmailTemplate.slug).all()
            for r in rows:
                session.expunge(r)
            return rows

    def upsert(self, slug: str, subject: str, html_body: str, description: str = "") -> EmailTemplate:
        """Insert or update the SYSTEM DEFAULT (partner_id IS NULL) row by slug. Used by seeder."""
        with session_scope() as session:
            t = session.query(EmailTemplate).filter(
                EmailTemplate.slug == slug, EmailTemplate.partner_id.is_(None),
            ).first()
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
        """Insert the SYSTEM DEFAULT only if slug doesn't already exist. Preserves
        admin-edited content on restarts. Used by seeder."""
        with session_scope() as session:
            existing = session.query(EmailTemplate).filter(
                EmailTemplate.slug == slug, EmailTemplate.partner_id.is_(None),
            ).first()
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
