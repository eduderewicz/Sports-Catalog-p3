from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Sport(Base):
    __tablename__ = 'sport'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    picture = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        '''Return object data in easily serializeable format'''
        return {
        'id': self.id,
        'name': self.name,
        'picture': self.picture,

}

class Position(Base):
    __tablename__ = 'position'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    sport_id = Column(Integer, ForeignKey('sport.id'))
    sport = relationship(Sport)
    @property
    def serialize(self):
        '''return object data in easily serializeable format'''
        return {
        'id': self.id,
        'name': self.name,
        'picture':self.picture,
}

class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    picture = Column(String(250))
    position_id = Column(Integer, ForeignKey('position.id'))
    position = relationship(Position)
    sport_id = Column(Integer, ForeignKey('sport.id'))
    sport = relationship(Sport)

    @property
    def serialize(self):
        '''Return object data in easily serializeable format'''
        return {
                'id': self.id,
                'name': self.name,
                "picture": self.picture,
                "position": self.position,

        }
engine = create_engine('sqlite:///allstars.db')

Base.metadata.create_all(engine)
