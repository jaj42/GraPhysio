# SQLAlchemy Bug: mssql column reflection silently drops columns with orphaned user_type_id

**Component:** `sqlalchemy.dialects.mssql` — table reflection  
**Regression introduced:** 2.0.42 (ticket #12654)  
**Last known good:** 2.0.41  
**Driver:** pymssql (reproduced with 2.3.2 and 2.3.13; likely affects all pymssql versions)

---

## Summary

Since 2.0.42, `Table(..., autoload_with=engine)` and `inspect(engine).get_columns()` silently
drop any column whose `sys.columns.user_type_id` has no matching row in `sys.types`. The dropped
columns produce no error and no warning unless the missing column is also referenced as an index
key. The root cause is an INNER JOIN to `sys.types` in the new reflection query; the previous
`information_schema.columns`-based query handled such columns correctly.

---

## Environment

```
sqlalchemy     2.0.42–2.0.50  (broken)
sqlalchemy     2.0.39–2.0.41  (working)
pymssql        2.3.2 / 2.3.13 (both affected)
Python         3.12
SQL Server     (Philips DWC — exact version unknown, standard SQL Server)
```

---

## Steps to reproduce

```python
from sqlalchemy import MetaData, Table, create_engine, inspect

engine = create_engine("mssql+pymssql://user:pass@host/dbname")

# Via autoload_with
meta = MetaData(schema="_Export")
t = Table("Wave_", meta, autoload_with=engine)
print(list(t.c.keys()))   # missing columns are silently absent

# Via inspect
cols = inspect(engine).get_columns("Wave_", schema="_Export")
print([c["name"] for c in cols])   # same missing columns
```

---

## Observed vs expected

### Expected (SQLAlchemy ≤ 2.0.41) — 22 columns

```
Id, TimeStamp, BasePhysioId, PhysioId, Label, Channel, SamplePeriod,
IsSlowWave, IsDerived, Color, LowEdgeFrequency, HighEdgeFrequency,
ScaleLower, ScaleUpper, CalibrationScaledLower, CalibrationScaledUpper,
CalibrationAbsLower, CalibrationAbsUpper, CalibrationType, UnitLabel,
UnitCode, EcgLeadPlacement
```

### Observed (SQLAlchemy ≥ 2.0.42) — 15 columns (7 silently missing)

```
Id, BasePhysioId, PhysioId, Channel, SamplePeriod, IsSlowWave, IsDerived,
Color, ScaleLower, ScaleUpper, CalibrationScaledLower, CalibrationScaledUpper,
CalibrationType, UnitCode, EcgLeadPlacement
```

### Missing columns and their types

| Column                 | SQL type          |
|------------------------|-------------------|
| `TimeStamp`            | `DATETIMEOFFSET`  |
| `Label`                | `NVARCHAR(50)`    |
| `LowEdgeFrequency`     | `NUMERIC(9, 3)`   |
| `HighEdgeFrequency`    | `NUMERIC(9, 3)`   |
| `CalibrationAbsLower`  | `NUMERIC(9, 3)`   |
| `CalibrationAbsUpper`  | `NUMERIC(9, 3)`   |
| `UnitLabel`            | `NVARCHAR(50)`    |

---

## Root cause

Ticket #12654 (released in 2.0.42) replaced the `information_schema.columns`-based reflection
query with one that queries `sys.columns` directly. The new query contains:

```sql
SELECT sys.columns.name, sys.types.name AS name_1, ...
FROM sys.columns
JOIN sys.types ON sys.columns.user_type_id = sys.types.user_type_id
...
WHERE sys.columns.object_id = object_id('[_Export].[Wave_]')
```

For the 7 missing columns, `sys.columns.user_type_id` holds values (262, 263, 265) that have
**no matching row in `sys.types`**:

```python
# Confirmed via raw query
conn.execute(text(
    "SELECT user_type_id, name FROM sys.types WHERE user_type_id IN (262, 263, 265)"
)).fetchall()
# → [] (empty — these type IDs are orphaned)
```

These are orphaned user-defined type alias IDs: the type aliases (`CREATE TYPE … FROM …`) were
defined when the table was created but have since been dropped (or were lost during a database
migration / restore). SQL Server preserves the `user_type_id` in `sys.columns` even after the
alias type is dropped. The INNER JOIN to `sys.types` therefore produces no row for those columns,
and they are silently omitted from the reflection result.

A `LEFT JOIN` with a fallback to `system_type_id` would be correct:

```sql
JOIN sys.types ON sys.columns.user_type_id = sys.types.user_type_id
```
→
```sql
LEFT JOIN sys.types AS ut ON sys.columns.user_type_id = ut.user_type_id
LEFT JOIN sys.types AS st ON sys.columns.system_type_id = st.user_type_id
    AND st.is_user_defined = 0
```

(and then use `COALESCE(ut.name, st.name)` for the type name).

The old `information_schema.columns` view handles orphaned types transparently because it reports
the effective SQL type rather than resolving through the type alias chain.

---

## Verification

```python
# LEFT JOIN manually confirms all 22 rows are reachable:
rows = conn.execute(text("""
    SELECT c.column_id, c.name, c.user_type_id, c.system_type_id, t.name AS type_name
    FROM sys.columns c
    LEFT JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = object_id('[_Export].[Wave_]')
    ORDER BY c.column_id
""")).fetchall()
# → 22 rows; missing columns have type_name = None (orphaned alias)
#   but the row itself is present and usable via system_type_id
```

---

## Workaround

Pin SQLAlchemy to ≤ 2.0.41 until the fix is available:

```toml
# pyproject.toml
[project.optional-dependencies]
dwc = ["sqlalchemy<2.0.42", ...]
```
