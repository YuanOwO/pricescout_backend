from sqlalchemy import BigInteger, Column, Double, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = "sqlite:///./data/product.db"

Base = declarative_base()

engine = create_engine(DB_URL, pool_size=20, max_overflow=0)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    pid = Column(BigInteger)
    pno = Column(String(20), nullable=True)
    barcode = Column(String(20), nullable=True)
    name = Column(String(100))
    price = Column(Integer)
    spec = Column(Double)
    unit = Column(String(10))
    price_unit = Column(Double)
    channel = Column(String(20))
    category1 = Column(String(20))
    category2 = Column(String(20))
    category3 = Column(String(20))
    url = Column(String(300))
    pic_url = Column(String(300))


def create_table():
    Base.metadata.create_all(engine)


def drop_table():
    Base.metadata.drop_all(engine)


def create_session():
    Session = sessionmaker(bind=engine)
    session = Session()

    return session
