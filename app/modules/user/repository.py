from app.db.base_repository import CRUDBase
from app.modules.user.models import User

class UserRepository(CRUDBase[User]):
    def __init__(self):
        super().__init__(model=User, collection_name="user")

user_repo = UserRepository()
