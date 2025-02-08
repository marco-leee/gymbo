from repo.Mongo import MongoDB
from repo.Repo import CoreRepo
from repo import ExerciseRepo, Exercise


class MongoCoreRepo(MongoDB, CoreRepo):
    def __init__(self, conn_str: str, db: str):
        super().__init__(conn_str, db)

    def update_exercise(self, exercise: Exercise):
        pass

    def update_media(self, media):
        pass
