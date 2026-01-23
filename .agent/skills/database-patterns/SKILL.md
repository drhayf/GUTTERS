---
name: database-patterns
description: Database patterns for GUTTERS. Use when creating models, migrations, or queries. Ensures JSONB for flexibility, proper indexes, and Alembic workflow.
---

# Database Patterns

SQLAlchemy 2.0 + Alembic patterns for GUTTERS. All configs stored as JSONB, migrations required for every change.

## Model Pattern
```python
from sqlalchemy import DateTime, String, JSONB, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db.database import Base
from datetime import datetime

class ModuleProfile(Base):
    __tablename__ = "module_profiles"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    
    # Foreign key (indexed)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        index=True
    )
    
    # JSONB for flexible data (REQUIRED for profiles/configs)
    data: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    config: Mapped[dict] = mapped_column(JSONB, default_factory=dict)
    
    # Timestamps (ALWAYS include)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None
    )
```

## JSONB Usage (Critical)
```python
# CORRECT - JSONB for flexibility
natal_chart: Mapped[dict] = mapped_column(JSONB)
config: Mapped[dict] = mapped_column(JSONB, default_factory=dict)

# Query JSONB
result = await db.execute(
    select(Profile).where(
        Profile.data["sun"]["sign"].astext == "Aries"
    )
)
```

## Migration Workflow
```bash
# 1. Create/modify model in models/
# 2. Generate migration
cd src && uv run alembic revision --autogenerate -m "add profiles table"

# 3. REVIEW generated migration in migrations/versions/
# 4. Edit if needed (Alembic isn't perfect)

# 5. Apply
uv run alembic upgrade head

# 6. Verify
uv run alembic current
```

## System Configurations Table
```python
class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    module_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # JSONB config (NEVER hardcode in code)
    config: Mapped[dict] = mapped_column(JSONB)
    
    # Optional: AI prompts
    prompt_template: Mapped[str | None] = mapped_column(Text)
    
    version: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)
```

## FastCRUD Pattern
```python
from fastcrud import FastCRUD

crud_profiles = FastCRUD[
    ModuleProfile,
    ProfileCreate,
    ProfileUpdate,
    ProfileUpdateInternal,
    ProfileDelete,
    ProfileRead
](ModuleProfile)

# Usage
profile = await crud_profiles.get(db=db, user_id=user_id)
await crud_profiles.create(db=db, object=profile_create)
```

## Critical Rules

- JSONB for ALL configs/profiles (flexibility)
- Index foreign keys
- Timestamps on all tables
- Review migrations before applying
- NEVER hardcode - store in `system_configurations`

See `references/migration-examples.md` for complex scenarios.