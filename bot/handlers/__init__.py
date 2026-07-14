from aiogram import Router

from .start import router as start_router
from .add import router as add_router
from .delete import router as delete_router
from .list import router as list_router
from .progress import router as progress_router
from .remind import router as remind_router
from .link import router as link_router
from .callback import router as callback_router

router = Router()

router.include_router(start_router)
router.include_router(add_router)
router.include_router(delete_router)
router.include_router(list_router)
router.include_router(progress_router)
router.include_router(remind_router)
router.include_router(link_router)
router.include_router(callback_router)