from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 数据库文件的路径
SQLALCHEMY_DATABASE_URL = "sqlite:///./app/data/nebula.db"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
