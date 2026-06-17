"""
Reusable helpers that apply the standard list request pattern
(global_filter / filters[] / sort_field / sort_order / skip / limit)
to any SQLAlchemy ORM query.
"""
from typing import Any, Dict, List, Tuple
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Query


def _apply_op(query: Query, col, operator: str, value: Any) -> Query:
    ops = {
        "equals":     lambda: query.filter(col == value),
        "notEquals":  lambda: query.filter(col != value),
        "contains":   lambda: query.filter(col.ilike(f"%{value}%")),
        "startsWith": lambda: query.filter(col.ilike(f"{value}%")),
        "endsWith":   lambda: query.filter(col.ilike(f"%{value}")),
    }
    fn = ops.get(operator)
    return fn() if fn else query


def apply_global_filter(query: Query, global_filter: str, columns: List) -> Query:
    """OR-ilike the search term across all supplied columns."""
    gf = (global_filter or "").strip()
    if not gf:
        return query
    pattern = f"%{gf}%"
    conditions = [col.ilike(pattern) for col in columns if col is not None]
    return query.filter(or_(*conditions)) if conditions else query


def apply_field_filters(query: Query, filters, column_map: Dict[str, Any]) -> Query:
    """Apply each FilterOption against column_map (field → SA column)."""
    for f in (filters or []):
        col = column_map.get(f.field)
        if col is None:
            continue
        query = _apply_op(query, col, f.operator, f.value)
    return query


def apply_sort(query: Query, model, sort_field: str, sort_order: int,
               default: str = "created_at") -> Query:
    sort_fn = desc if sort_order == -1 else asc
    col = getattr(model, sort_field, None) or getattr(model, default, None)
    return query.order_by(sort_fn(col)) if col is not None else query


def paginate(query: Query, skip: int, limit: int) -> Tuple[int, list]:
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return total, rows
