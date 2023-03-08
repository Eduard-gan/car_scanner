from pathlib import Path
from pydantic import BaseSettings


class Settings(BaseSettings):
    root_path: Path = Path()

    @property
    def db_path(self) -> Path:
        return self.root_path / 'db' / 'db.sqlite3'


settings = Settings()
