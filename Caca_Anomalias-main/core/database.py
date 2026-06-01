"""
Módulo: core/database.py
Descrição: Configura a conexão com o banco de dados SQLite via SQLAlchemy.
           Fornece engine, sessão e base declarativa para os modelos ORM.
Autor: Squad 4
Data: 2026
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Gerador de sessão de banco de dados.
    Garante que a sessão seja fechada ao término de cada requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
