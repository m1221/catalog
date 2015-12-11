from sqlalchemy import Table, Column, ForeignKey, Integer, String, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
  __tablename__ = 'user'
  
  name = Column(String(100))
  email = Column(String(100), primary_key = True)
  picture = Column(String(200))
  privilege = Column(String(20))

class Genre(Base):
  __tablename__ = 'genre'
  
  id = Column(Integer, primary_key = True, unique = True)
  name = Column(String(50), nullable = False, unique = True)
  description = Column(String(500))
  user_email = Column(String(100), ForeignKey('user.email'))
  user = relationship('User')
  
  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return {
      'name': self.name,
      'description': self.description
    }
  
class Publisher(Base):
  __tablename__ = 'publisher'
  
  id = Column(Integer, primary_key = True)
  name = Column(String(50), nullable = False, unique=True)
  description = Column(String(500))
  user_email = Column(String(100), ForeignKey('user.email'))
  user = relationship('User')
  
  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return {
      'name': self.name,
      'description': self.description
    }
  
class Game(Base):
  __tablename__ = 'game'
  
  id = Column(Integer, primary_key = True, unique = True)
  name = Column(String(50), nullable = False)
  
  genre_name = Column(Integer, ForeignKey('genre.name'))
  genre = relationship('Genre', backref='games')
  
  publisher_name = Column(Integer, ForeignKey('publisher.name'))
  publisher = relationship('Publisher', backref='games')
  
  user_email = Column(String(100), ForeignKey('user.email'))
  user = relationship('User', backref='users')
  
  release_date = Column(Date)
  description = Column(String(500))
  rating = Column(String(7))
  market_value = Column(String(6))
  mv_date = Column(Date)
  pic_url = Column(String(60))
  
  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return {
      'name': self.name,
      'description': self.description,
      'genre': self.genre.name,
      'publisher': self.publisher.name,
      'release_date': str(self.release_date),
      'rating': self.rating,
      'market_value': self.market_value,
      'mv_date': str(self.mv_date),
      'pic_url': self.pic_url
    }
  
### End of file ###
engine = create_engine('sqlite:///icgdb.db')
Base.metadata.create_all(engine)