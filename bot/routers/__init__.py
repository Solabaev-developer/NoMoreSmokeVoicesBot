# bot/routers/__init__.py
from .start       import router as start_router
from .new_sticker import router as new_sticker_router
from .inline_search import router as inline_router
from .delete_sticker import router as delete_sticker_router
from .search_by_tags import router as search_by_tags_router

__all__ = (
    "start_router",
    "new_sticker_router",
    "inline_router",
    "delete_sticker_router",
    "search_by_tags_router"
)