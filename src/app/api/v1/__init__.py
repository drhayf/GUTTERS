from fastapi import APIRouter

from .birth_data import router as birth_data_router
from .genesis import router as genesis_router
from .health import router as health_router
from .intelligence import router as intelligence_router
from .login import router as login_router
from .logout import router as logout_router
from .memory import router as memory_router
from .observability import router as observability_router
from .posts import router as posts_router
from .rate_limits import router as rate_limits_router
from .tasks import router as tasks_router
from .tiers import router as tiers_router
from .users import router as users_router
from .tracking import router as tracking_router
from .observer import router as observer_router
from .synthesis import router as synthesis_router
from .hypothesis import router as hypothesis_router
from .vector import router as vector_router
from .chat import router as chat_router

router = APIRouter(prefix="/v1")
router.include_router(birth_data_router)
router.include_router(genesis_router)
router.include_router(health_router)
router.include_router(intelligence_router)
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(memory_router)
router.include_router(observability_router)
router.include_router(users_router)
router.include_router(posts_router)
router.include_router(tasks_router)
router.include_router(tiers_router)
router.include_router(rate_limits_router)
router.include_router(tracking_router)
router.include_router(observer_router)
router.include_router(synthesis_router)
router.include_router(hypothesis_router)
router.include_router(vector_router)
router.include_router(chat_router)
