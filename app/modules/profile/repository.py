from app.db.base_repository import CRUDBase
from app.modules.profile.models import Profile
from app.utils.app_constant import COLL_TODO_PROFILE

class ProfileRepository(CRUDBase[Profile]):
    def __init__(self):
        super().__init__(model=Profile, collection_name=COLL_TODO_PROFILE)

profile_repo = ProfileRepository()
