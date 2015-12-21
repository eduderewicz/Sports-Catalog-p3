from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Sport, Position, Player
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
"""
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"
"""

# Connect to Database and create database session
engine = create_engine('sqlite:///allstars.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# JSON APIs to view Sport Information
@app.route('/sport/<int:sport_id>/player/JSON')
def sportPlayerJSON(sport_id):
    sport = session.query(Sport).filter_by(id=sport_id).one()
    items = session.query(Player).filter_by(
        sport_id=sport_id).all()
    return jsonify(Player=[i.serialize for i in items])




# Show all Sports
@app.route('/')

@app.route('/sports/')
def showSports():
    sports = session.query(Sport).order_by(asc(Sport.name))
    #if 'username' not in login_session:
    #    return render_template('publicrestaurants.html', restaurants=restaurants)
    #else:
    
    return render_template('publicsports.html', sports=sports)

# add new sport
@app.route('/sports/new/', methods=['GET','POST'])
def newSport():
    if request.method == 'POST':
        newSport = Sport(
            name = request.form['name'])
        session.add(newSport)
        flash('New Sport %s Successfully Created' % newSport.name)
        session.commit()
        return redirect(url_for('showSports'))
    else:
        return render_template('newSport.html')

#edit a sport
@app.route('/sport/<int:sport_id>/edit/', methods = ['GET', 'POST'])
def editSport(sport_id):
    editedSport = session.query(
        Sport).filter_by(id = sport_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedSport.name = request.form['name']
            session.add(editedSport)
            session.commit()
            flash('Sport Successfully Edited %s' % editedSport.name)
            return redirect(url_for('showSports'))
    else:
        return render_template('editSport.html', sport = editedSport)

#add position (for a sport)
@app.route('/sport/<int:sport_id>/positions/new/', methods = ['GET', 'POST'])
def addPosition(sport_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()

    if request.method == 'POST':
        newPosition = Position(name = request.form['name'],
            sport_id = sport_id)
        session.add(newPosition)
        session.commit()
        flash('New Position %s Successfully Added' % (newPosition.name))
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:
        return render_template('newPosition.html', sport_id = sport_id)

    
#edit position (for a sport)
@app.route('/sport/<int:sport_id>/positions/<int:position_id>/edit/', methods = ['GET', 'POST'])
def editPosition(sport_id, position_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    editedPosition =  session.query(Position).filter_by(id = position_id).one()

    if request.method == 'POST':
        if request.form['name']:
            editedPosition.name = request.form['name']
        session.add(editedPosition)
        session.commit()
        flash('Position Successfully Edited')
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:
        return render_template('editPosition.html', sport = sport, position = editedPosition)




#delete position (for a sport)
@app.route('/sport/<int:sport_id>/positions/<int:position_id>/delete/', methods = ['GET', 'POST'])
def deletePosition(sport_id, position_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    positionToDelete = session.query(Position).filter_by(id = position_id).one()

    if request.method == 'POST':
        #delete players at that position before deleting position 

        playerCount = session.query(Player).filter_by(position_id = position_id).count()
        for i in range(1,playerCount + 1):
            playerToDelete = session.query(Player).filter_by(position_id = position_id).first()            
            if playerToDelete.position_id == positionToDelete.id:
                session.delete(playerToDelete)
                flash ('%s Successfully Deleted' % playerToDelete.name )
                session.commit

        #delete position
        session.delete(positionToDelete)
        flash ('%s Successfully Deleted' % positionToDelete.name)
        session.commit()
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:
        return render_template ('deletePosition.html', sport = sport, position = positionToDelete )

# Show all players
@app.route('/sport/<int:sport_id>/')
@app.route('/sport/<int:sport_id>/players/')
def showPlayers(sport_id):
    sports = session.query(Sport).filter_by(id=sport_id).one()
    #creator = getUserInfo(restaurant.user_id)
    players = session.query(Player).filter_by(
        sport_id=sport_id).all()
    positions = session.query(Position).filter_by(
        sport_id = sport_id).all()

    #positions = session.query(Player).filter_by(
    #	id = player_id).all()
    #if 'username' not in login_session or creator.id != login_session['user_id']:
    #    return render_template('publicmenu.html', items=items, restaurant=restaurant, creator=creator)
    #else:
    return render_template('publicplayers.html', players = players, sports = sports, positions = positions)
        #return render_template('player.html', items=items, restaurant=restaurant, creator=creator)

#add a player
@app.route('/sport/<int:sport_id>/players/new', methods = ['GET', 'POST'])
def newPlayer(sport_id):

    sport = session.query(Sport).filter_by(id = sport_id).one()
    positions = session.query(Position).filter_by(sport_id = sport_id).all()

    if request.method == 'POST':
        
        newPlayer = Player(name=request.form['name'], 
            picture = request.form['picture'],
            position_id = request.form['position'],
            sport_id = sport_id)
       
        session.add(newPlayer)
        session.commit()
        flash('New Player %s Successfully Added' % (newPlayer.name))
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:  
        return render_template('newPlayer.html', sport_id = sport_id, positions = positions)

#edit a player
@app.route('/sport/<int:sport_id>/players/<int:player_id>/edit/', methods = ['GET','POST'])
def editPlayer(sport_id, player_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    playerToEdit = session.query(Player).filter_by(id = player_id).one()
    positions = session.query(Position).filter_by(sport_id = sport_id).all()


    if request.method == 'POST':
        if request.form['name']:
            playerToEdit.name = request.form['name']
        if request.form['picture']:
            playerToEdit.picture = request.form['picture']
        if request.form['position']:
            playerToEdit.position_id = request.form['position']


        
        flash('Played Successfully Edited')
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:
        return render_template('editPlayer.html', sport = sport, player = playerToEdit, positions = positions)

#delete a player
@app.route('/sport/<int:sport_id>/players/<int:player_id>/delete/', methods = ['GET', 'POST'])
def deletePlayer(sport_id,player_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    playerToDelete = session.query(Player).filter_by(id = player_id).one()

    if request.method == 'POST':
        session.delete(playerToDelete)
        session.commit
        flash ('%s Successfully Deleted' % playerToDelete.name )
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:
        return render_template ('deletePlayer.html', sport = sport, player = playerToDelete)



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)