"""时间工具：统一 UTC 处理，避免与 MySQL 服务器本地时区混淆。

## 我们的约定
- **DB 列里所有 datetime 都存 UTC**（应用层显式 `datetime.now(tz=timezone.utc)` 写入；
  ORM 端 `server_default` / `onupdate` 用 `func.utc_timestamp()`）。
- **MySQL DATETIME 列本身不带时区**，asyncmy 把 timezone-aware 写入时去掉 tzinfo，
  读出来是 naive datetime——按约定就把它当作 UTC 即可。
- **对外输出（DTO 里的 isoformat 字符串）必须带 UTC 时区后缀 `+00:00`**，
  否则 JS `new Date(...)` 会按浏览器本地时区解析，看上去就比北京时间慢 8 小时。

## 不在这里做的事
- 我们 *不* 在后端把时间转成北京时间字符串返回，而是统一返回 UTC ISO 8601；
- 前端用 `new Date(isoStr).toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai'})`
  之类的方式按用户本地时区展示，互不耦合。
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """当前 UTC 时间（aware）。所有写入 DB 的时间都该走这里。"""
    return datetime.now(tz=timezone.utc)


def to_utc_iso(dt: datetime | None) -> str | None:
    """把 ORM 读出来的 datetime 转成带 UTC 标记的 ISO 字符串。

    DB 列存的是 naive datetime（按约定值是 UTC），这里强制贴上 tzinfo=UTC
    再 isoformat()，输出形如 ``2026-05-11T03:24:53+00:00``，前端 ``new Date()``
    可以无歧义地解析为正确的 UTC 瞬间，再渲染成用户本地时区。

    若 dt 是 None，返回 None（方便给 finished_at 这种可选列直接用）。
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()
