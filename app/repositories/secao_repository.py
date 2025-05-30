from app.db.orm_models import Secao
from app.repositories.base_repository import BaseRepository

class SecaoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Secao)

    def get(self, id):
        return self.db.query(Secao).filter(Secao.id == id).first()

    def list(self):
        return self.db.query(Secao).all()
