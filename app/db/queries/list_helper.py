"""
Reusable helpers that apply the standard list request pattern
(global_filter / filters[] / sort_field / sort_order / skip / limit)
to any SQLAlchemy ORM query.
"""
from typing import Any, Dict, List, Tuple
from sqlalchemy import asc, desc, or_, cast
from sqlalchemy.orm import Query


def _coerce(col, value: Any):
    """gte/lte/between values arrive as plain strings from JSON (e.g. "2026-07-20"
    for a Date column) — cast them to the column's own SQL type so Postgres doesn't
    reject a bare varchar-vs-date/int comparison."""
    return cast(value, col.type)


def _apply_op(query: Query, col, operator: str, value: Any) -> Query:
    ops = {
        "equals":     lambda: query.filter(col == value),
        "notEquals":  lambda: query.filter(col != value),
        "contains":   lambda: query.filter(col.ilike(f"%{value}%")),
        "startsWith": lambda: query.filter(col.ilike(f"{value}%")),
        "endsWith":   lambda: query.filter(col.ilike(f"%{value}")),
        "gte":        lambda: query.filter(col >= _coerce(col, value)),
        "lte":        lambda: query.filter(col <= _coerce(col, value)),
        "between":    lambda: query.filter(col.between(_coerce(col, value[0]), _coerce(col, value[1])))
                      if isinstance(value, (list, tuple)) and len(value) == 2 else query,
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
    """Apply each FilterOption against column_map (field → SA column, or a
    callable (query, filter_option) -> query for filters that need custom
    logic, e.g. an EXISTS subquery across a join table)."""
    for f in (filters or []):
        col = column_map.get(f.field)
        if col is None:
            continue
        if callable(col):
            query = col(query, f)
        else:
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
