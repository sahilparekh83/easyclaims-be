from typing import Optional, List
from ..models.whatsapp_template import WhatsAppTemplate
from ..session import session_scope


class WhatsAppTemplateQuery:
    def get_by_slug(self, slug: str) -> Optional[WhatsAppTemplate]:
        """System default template for this slug (partner_id IS NULL)."""
        with session_scope() as session:
            t = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.slug == slug,
                WhatsAppTemplate.partner_id.is_(None),
                WhatsAppTemplate.is_active == True,
            ).first()
            if t:
                session.expunge(t)
            return t

    def get_for_partner(self, slug: str, partner_id: Optional[str]) -> Optional[WhatsAppTemplate]:
        """Partner-specific override if one is set and active, else the system default."""
        if partner_id:
            with session_scope() as session:
                t = session.query(WhatsAppTemplate).filter(
                    WhatsAppTemplate.slug == slug,
                    WhatsAppTemplate.partner_id == partner_id,
                    WhatsAppTemplate.is_active == True,
                ).first()
                if t:
                    session.expunge(t)
                    return t
        return self.get_by_slug(slug)

    def list_overrides_for_slug(self, slug: str) -> List[WhatsAppTemplate]:
        with session_scope() as session:
            rows = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.slug == slug,
                WhatsAppTemplate.partner_id.isnot(None),
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def create_override(self, slug: str, partner_id: str, meta_template_name: str = None,
                        meta_template_language: str = "en", description: str = "") -> WhatsAppTemplate:
        with session_scope() as session:
            existing = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.slug == slug, WhatsAppTemplate.partner_id == partner_id,
            ).first()
            if existing:
                raise ValueError(f"An override for '{slug}' already exists for this partner")
            default = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.slug == slug, WhatsAppTemplate.partner_id.is_(None),
            ).first()
            t = WhatsAppTemplate(
                slug=slug, partner_id=partner_id,
                meta_template_name=meta_template_name,
                meta_template_language=meta_template_language,
                description=description,
                header_type=default.header_type if default else None,
                variable_order=default.variable_order if default else [],
            )
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def delete_override(self, template_id: str) -> bool:
        """Delete a partner override only — system default templates (partner_id NULL) cannot be deleted."""
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.id == _uuid.UUID(str(template_id)),
                WhatsAppTemplate.partner_id.isnot(None),
            ).first()
            if not t:
                return False
            session.delete(t)
            return True

    def get_by_id(self, template_id: str) -> Optional[WhatsAppTemplate]:
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.id == _uuid.UUID(str(template_id))
            ).first()
            if t:
                session.expunge(t)
            return t

    def list_all(self, partner_id: Optional[str] = None) -> List[WhatsAppTemplate]:
        """By default lists only system-default templates. Pass partner_id to also
        include that partner's overrides (used by the admin UI's per-partner view)."""
        with session_scope() as session:
            q = session.query(WhatsAppTemplate)
            if partner_id:
                q = q.filter(
                    (WhatsAppTemplate.partner_id.is_(None)) | (WhatsAppTemplate.partner_id == partner_id)
                )
            else:
                q = q.filter(WhatsAppTemplate.partner_id.is_(None))
            rows = q.order_by(WhatsAppTemplate.slug).all()
            for r in rows:
                session.expunge(r)
            return rows

    def create_if_not_exists(self, slug: str, variable_order: List[str], header_type: str = None,
                             description: str = "") -> WhatsAppTemplate:
        """Insert the SYSTEM DEFAULT only if slug doesn't already exist. Preserves
        admin-edited (meta_template_name etc.) content on restarts. Used by seeder."""
        with session_scope() as session:
            existing = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.slug == slug, WhatsAppTemplate.partner_id.is_(None),
            ).first()
            if existing:
                session.expunge(existing)
                return existing
            t = WhatsAppTemplate(
                slug=slug, variable_order=variable_order, header_type=header_type,
                description=description,
            )
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def update(self, template_id: str, **kwargs) -> Optional[WhatsAppTemplate]:
        import uuid as _uuid
        with session_scope() as session:
            t = session.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.id == _uuid.UUID(str(template_id))
            ).first()
            if not t:
                return None
            for k, v in kwargs.items():
                setattr(t, k, v)
            session.flush()
            session.expunge(t)
            return t
