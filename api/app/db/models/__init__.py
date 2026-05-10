"""ORM 模型聚合包。

这里集中导出所有 SQLAlchemy 模型类，方便其它模块统一 from 这里 import。
新增模型时:
1. 在本目录新建 `xxx.py` 并定义 `XxxORM(Base)`
2. 在 __init__.py 里 re-export
3. 在 app/db/base.py 里 import,让 Alembic autogenerate 能发现
"""

from app.db.models.project import ProjectORM
from app.db.models.scene import SceneORM
from app.db.models.user import UserORM
from app.db.models.video_detail import VideoDetailORM
from app.db.models.video_task import VideoTaskORM

__all__ = [
    "ProjectORM",
    "SceneORM",
    "UserORM",
    "VideoDetailORM",
    "VideoTaskORM",
]
