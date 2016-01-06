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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sports Catalog"


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

#setup Google oAuth
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



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
    if 'username' not in login_session:
        return render_template('publicsports.html', sports=sports)
    #else:
    
    return render_template('sports.html', sports=sports)

# add new sport
@app.route('/sports/new/', methods=['GET','POST'])
def newSport():
    if request.method == 'POST':
        newSport = Sport(
            name = request.form['name'],
            user_id = login_session['user_id'])
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
    creator = getUserInfo(editedSport.user_id)
    if request.method == 'POST':
        if request.form['name']:
            editedSport.name = request.form['name']
            session.add(editedSport)
            session.commit()
            flash('Sport Successfully Edited %s' % editedSport.name)
            return redirect(url_for('showPlayers', sport_id = sport_id))
    
    #if not logged in this page should not be viewable, redirect to public page  
    if 'username' not in login_session:
        flash('login to add/edit/delete players')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    # if this user is not the creator of the sport, they cannot edit the sport, redirect to the logged in players page
    if creator.id != login_session['user_id']:
        flash('You cannot edit a sport you did not create')
        return redirect(url_for('showPlayers', sport_id = sport_id))    


    else:
        return render_template('editSport.html', sport = editedSport)

#add position (for a sport)
@app.route('/sport/<int:sport_id>/positions/new/', methods = ['GET', 'POST'])
def addPosition(sport_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()

    creator = getUserInfo(sport.user_id)

    if request.method == 'POST':
        newPosition = Position(name = request.form['name'],
            sport_id = sport_id)
        session.add(newPosition)
        session.commit()
        flash('New Position %s Successfully Added' % (newPosition.name))
        return redirect(url_for('showPlayers', sport_id = sport_id))
    
    #if not logged in this page should not be viewable, redirect to public page  
    if 'username' not in login_session:
        flash('login to add/edit/delete players')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    # if this user is not the creator of the sport, they cannot delete the positions, redirect to the logged in players page
    if creator.id != login_session['user_id']:
        flash('You cannot add a position for a sport you did not create')
        return redirect(url_for('showPlayers', sport_id = sport_id))
 
    else:
        return render_template('newPosition.html', sport_id = sport_id)

    
#edit a position (for a sport)
@app.route('/sport/<int:sport_id>/positions/<int:position_id>/edit/', methods = ['GET', 'POST'])
def editPosition(sport_id, position_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    editedPosition =  session.query(Position).filter_by(id = position_id).one()

    creator = getUserInfo(sport.user_id)
    
    if request.method == 'POST':
        if request.form['name']:
            editedPosition.name = request.form['name']
        session.add(editedPosition)
        session.commit()
        flash('Position Successfully Edited')
        return redirect(url_for('showPlayers', sport_id = sport_id))
    
    #if not logged in this page should not be viewable, redirect to public page  
    if 'username' not in login_session:
        flash('login to add/edit/delete positions')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    # if this user is not the creator of the sport, they cannot edit the positions, redirect to the logged in players page
    if creator.id != login_session['user_id']:
        flash('You cannot edit a position you did not create')
        return redirect(url_for('showPlayers', sport_id = sport_id))
 
    else:
        return render_template('editPosition.html', sport = sport, position = editedPosition)




#delete position (for a sport)
@app.route('/sport/<int:sport_id>/positions/<int:position_id>/delete/', methods = ['GET', 'POST'])
def deletePosition(sport_id, position_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    positionToDelete = session.query(Position).filter_by(id = position_id).one()
    creator = getUserInfo(sport.user_id)

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
    
    #if not logged in this page should not be viewable, redirect to public page  
    if 'username' not in login_session:
        flash('login to add/edit/delete positions')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    # if this user is not the creator of the sport, they cannot delete the positions, redirect to the logged in players page
    if creator.id != login_session['user_id']:
        flash('You cannot delete a position you did not create')
        return redirect(url_for('showPlayers', sport_id = sport_id))

    else:
        return render_template ('deletePosition.html', sport = sport, position = positionToDelete )

# Show all players
@app.route('/sport/<int:sport_id>/')
@app.route('/sport/<int:sport_id>/players/')
def showPlayers(sport_id):
    sports = session.query(Sport).filter_by(id=sport_id).one()
    creator = getUserInfo(sports.user_id)
    players = session.query(Player).filter_by(
        sport_id=sport_id).all()
    positions = session.query(Position).filter_by(
        sport_id = sport_id).all()

#or creator.id != login_session['user_id']  
    if 'username' not in login_session:
        return render_template('publicplayers.html', players = players, sports = sports, positions = positions)
    else:
        return render_template('players.html', players = players, sports = sports, positions = positions)
        

#add a player
@app.route('/sport/<int:sport_id>/players/new', methods = ['GET', 'POST'])
def newPlayer(sport_id):

    sport = session.query(Sport).filter_by(id = sport_id).one()
    positions = session.query(Position).filter_by(sport_id = sport_id).all()

    if request.method == 'POST':
        
        newPlayer = Player(name=request.form['name'], 
            picture = request.form['picture'],
            position_id = request.form['position'],
            sport_id = sport_id,
            user_id = login_session['user_id'])
       
        session.add(newPlayer)
        session.commit()
        flash('New Player %s Successfully Added' % (newPlayer.name))
        return redirect(url_for('showPlayers', sport_id = sport_id))
    if not positions:
        flash('At least one position must exist prior to adding a player')
        return redirect(url_for('showPlayers', sport_id = sport_id))
    else:  
        return render_template('newPlayer.html', sport_id = sport_id, positions = positions)

#edit a player
@app.route('/sport/<int:sport_id>/players/<int:player_id>/edit/', methods = ['GET','POST'])
def editPlayer(sport_id, player_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    playerToEdit = session.query(Player).filter_by(id = player_id).one()
    positions = session.query(Position).filter_by(sport_id = sport_id).all()
    creator = getUserInfo(playerToEdit.user_id)

    if request.method == 'POST':
        if request.form['name']:
            playerToEdit.name = request.form['name']
        if request.form['picture']:
            playerToEdit.picture = request.form['picture']
        if request.form['position']:
            playerToEdit.position_id = request.form['position']
        flash('Played Successfully Edited')

    #if not logged in this page should not be viewable, redirect to public page  
    if 'username' not in login_session:
        flash('login to add/edit/delete players')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        

    # if this user is not the creator, they cannot edit the player, redirect to the logged in players page
    if creator.id != login_session['user_id']:
        flash('You cannot edit a player you did not create')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    else:
        return render_template('editPlayer.html', sport = sport, player = playerToEdit, positions = positions)

#delete a player
@app.route('/sport/<int:sport_id>/players/<int:player_id>/delete/', methods = ['GET', 'POST'])
def deletePlayer(sport_id,player_id):
    sport = session.query(Sport).filter_by(id = sport_id).one()
    playerToDelete = session.query(Player).filter_by(id = player_id).one()
    creator = getUserInfo(playerToDelete.user_id)

    if request.method == 'POST':
        session.delete(playerToDelete)
        session.commit
        flash ('%s Successfully Deleted' % playerToDelete.name )
        return redirect(url_for('showPlayers', sport_id = sport_id))

    if 'username' not in login_session:
        flash('login to add/edit/delete players')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    # if this user is not the creator, they cannot delete the player, redirect to the logged in players page
    if creator.id != login_session['user_id']:
        flash('You cannot delete a player you did not create')
        return redirect(url_for('showPlayers', sport_id = sport_id))
        
    else:
        return render_template ('deletePlayer.html', sport = sport, player = playerToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showSports'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showSports'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)