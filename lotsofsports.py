from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Sport, Position, Player

engine = create_engine('sqlite:///allstars.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#Create dummy user
user1 = User(id = 1, name= "Bob the User", email="none")
session.add(user1)
session.commit()


#Create sport - Basketball
sport1 = Sport(id = 1, name = "Basketball", picture = 'http://ecx.images-amazon.com/images/I/81fi%2BmmwnaL.jpg', user_id = 1)
session.add(sport1)
session.commit()

#Create positions in basketball
positionPG = Position(id = 1, name = "PG", sport_id = 1, user_id = 1)
session.add(positionPG)
session.commit()

positionSG = Position(id = 2, name = "SG", sport_id = 1, user_id = 1)
session.add(positionSG)
session.commit()

positionSF = Position(id =3, name = "SF", sport_id = 1, user_id = 1)
session.add(positionSF)
session.commit()

positionPF = Position(id =  4, name = "PF", sport_id = 1, user_id = 1)
session.add(positionPF)
session.commit()

positionC = Position(id = 5, name = "C", sport_id = 1, user_id = 1)
session.add(positionC)
session.commit()


#Players in basketball
player1 = Player(name="Kevin Durant", picture = 'http://cdn.slamonline.com/wp-content/uploads/2015/01/kevin-durant1-600x387.jpg', 
	position_id = 3, sport_id = 1, user_id = 1)
session.add(player1)
session.commit()

player2 = Player(name = "Steph Curry", picture = 'http://www.gannett-cdn.com/-mm-/4a3a44a51060a252e5652ab3b0de8f75a0998627/c=1203-0-3795-3456&r=537&c=0-0-534-712/local/-/media/2015/02/12/USATODAY/USATODAY/635593043210421208-USATSI-8272280.jpg',
	position_id = 1, sport_id = 1, user_id = 1)
session.add(player2)
session.commit()
print "added players"