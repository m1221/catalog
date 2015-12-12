"""This module creates the sqlite DB for the ICGDB web app.

License: GPLv3
Module Description: This module uses SQLAlchemy to create an SQL database for
the Internet Computer Game Database (ICGDB) web application. This module
establishes four tables (Game, User, Genre, Publisher) which will be queried
and modified by the web application. The database may be populated with games,
users, genres, and publishers by running the db_populate module.

For more information regarding the use of SQLAlchemy in this module, please
visit the SQLAlchemy ORM documentation.

This package was created to satisfy the Udacity Full Stack Nanodegree
requirement for the Catalog project.
"""

from sqlalchemy import Table, Column, ForeignKey, Integer, String, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# This declarative lets SQLAlchemy know that our classes are special SQL
# classes that correspond to values in our database.
Base = declarative_base()

class User(Base):
    """The User class is mapped to the 'user' table in the database.
    
    The 'user' table contains information about users. Users can log into the
    web app and make changes to the database.
  
    Attributes:
        email: an up-to 100char string containing the email address of the user.
               email serves as its PRIMARY KEY in the 'user' table.
        name: an up-to 100char string containing the name of the user
        picture: an up-to 200char string containing a url to the user's picture
        privilege: an up-to 20char string containing a descriptor of the user's
                   privilege. 
                   If this field is blank, then the user can ONLY
                   add/edit/remove content that the user has added.
                   If this field is 'superuser', then the user can
                   add/edit/remove ALL content.  
    """
    __tablename__ = 'user'
  
    name = Column(String(100))
    email = Column(String(100), primary_key = True)
    picture = Column(String(200))
    privilege = Column(String(20))

    
class Game(Base):
    """The Game class is mapped to the 'game' table in the database.
    
    The 'game' table contains information about games. 
  
    Attributes:
        id: an integer value. id serves as a PRIMARY KEY in the 'game' table.
        name: an up-to 50char string containing the name of the game.
        genre_name: an up-to 50char string containing the genre of the game.
        publisher_name: an up-to50 char string containing the publisher of 
                        the game.
        user_email: an up-to 100char string containing the email of the user
                    that entered the game into the database.
        release_date: a date value containing the release date of the game.
        description: an up-to 500char string containing a description of the
                     game.
        rating: an up-to 7char string containing the rating of the game. The 
                format should be xx/100.
        market_value: an up-to 6char string containing the market value of the
                      game. The format should be $xx. 
        mv_date: a date value entered when the market value of the game was
                 last determined.
        pic_url: an up-to 60char string containing the url for the game's
                 picture.
    """
    __tablename__ = 'game'
    
    id = Column(Integer, primary_key = True, unique = True)
    name = Column(String(50), nullable = False)
    
    genre_name = Column(String(50), ForeignKey('genre.name'))
    genre = relationship('Genre', backref='games')
    
    publisher_name = Column(String(50), ForeignKey('publisher.name'))
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

        
class Genre(Base):
    """The Genre class is mapped to the 'genre' table in the database.
    
    The 'genre' table contains information about genres. 
  
    Attributes:
        id: an integer value. id serves as a PRIMARY KEY in the 'publisher' table.
        name: an up-to 50char string containing the name of the genre.
        description: an up-to 500char string containing a description of the
                     genre.
        user_email: an up-to 100char string containing the email of the user
                    that entered the genre into the database.
    """
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
    """The Publisher class is mapped to the 'publisher' table in the database.
    
    The 'publisher' table contains information about genres. 
  
    Attributes:
        id: an integer value. id serves as a PRIMARY KEY in the 'publisher' table.
        name: an up-to 50char string containing the name of the publisher.
        description: an up-to 500char string containing a description of the
                     publisher.
        user_email: an up-to 100char string containing the email of the user
                    that entered the publisher into the database.
    """
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

### End of file ###
engine = create_engine('sqlite:///icgdb.db') # create OR connect to the DB
Base.metadata.create_all(engine) # add classes as tables in the database