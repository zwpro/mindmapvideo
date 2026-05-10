"""统一收集所有 ORM 模型，供 Alembic autogenerate 使用。

Alembic env.py 里 `from app.db.base import Base` 触发本模块加载,
所有在这里被 import 的 ORM 类都会注册到 Base.metadata。

新增模型 -> 在 app/db/models/ 里建文件 -> 在这里追加一行 import。
"""

from app.db.session import Base  # noqa: F401

# 所有 ORM 模型必须在此处 import,Alembic 才能在 autogenerate 时看到。
from app.db.models import (  # noqa: F401
    ProjectORM,
    SceneORM,
    UserORM,
    VideoDetailORM,
    VideoTaskORM,
)
