from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy_history import make_versioned

make_versioned(user_cls=None)

Base = declarative_base()
