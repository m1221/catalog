"""This module serves the ICGDB web application.

License: GPLv3
Module Description: This module uses the Flask Framework to serve the Internet
Computer Game Database (ICGDB) web application. 
Features of the web application (html, css, and server module) include:
    -3rd party Oauth via GooglePlus
    -JSON and XML endpoints
        - JSON and XML endpoints exists for Games, Game, Genres, and Publishers pages
        - to access an endpoint, add 'JSON' or 'XML' to the end of the url of a page
            eg: localhost:5000/main/publishers/XML
    -Responsive Design for mobile, tablet, and pc/laptop
    -Jinja2 templates to simplify modification to HTML files
    -CSRF defense via Flask-SeaSurf

For more information regarding the use of the Flask Framework please review the
Flask and Jinja2 documentation.

I HIGHLY RECOMMEND THAT THE REVIEWER ATTEMPT TO USE THE WEB APP AND BROWSE
THROUGH THE NAMES OF THE HTML DOCS BEFORE LOOKING AT THIS CODE.

This package was created to satisfy the Udacity Full Stack Nanodegree
requirement for the Catalog project.
"""

import os
from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from icgdb_database_setup import Base, Game, Publisher, Genre, User

# Oauth Imports
import random, string
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, Credentials
import oauth2client.client
import httplib2
import json
import requests

# Security Imports
import bleach #
from werkzeug import secure_filename #

# XML endpoint import
import xml.etree.ElementTree as ET

### END IMPORTS

# Connect to db
engine = create_engine('sqlite:///icgdb.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# SETUP AND CONFIGURATION FOR FILE(IMAGE) UPLOAD
UPLOAD_FOLDER = os.path.abspath('static/pics')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 # limit size to 100kb

def checkExtension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def uploadFile():
    file = request.files['game-image']
    if file and checkExtension(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename

        
# OAUTH SETUP FOR GOOGLE
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'ICGDB'

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        respose = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    code = request.data # get code from client
    try: # getting access token from server
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code) # send code to server and get acess token
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the '
                                            'authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

 
    login_session['access_token'] = credentials.access_token
    access_token = credentials.access_token
    url =('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'% access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1]) # use access token to get info from server

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    gplus_id = credentials.id_token['sub'] # server information. 
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
  
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match"
                                            "the app's client ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
  
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
   
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id
  
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
 
    data = answer.json()
    
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    email = checkEmail(login_session['email'])
    if not email:
        createUser(login_session['email'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s." % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'),
                                            401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # execute HTTP GET request to revoke current token
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] =='200':
        # remove user information from session
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    else:
        # for an unknown reason, access token was invalid
        response = make_response(json.dumps('Failed to revoke token for'
                                            'given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
    
# END OAUTH SETUP #

### BEGIN PAGE ROUTING

# ORGANIZATION OF FUNCTIONS
#--------------------------------------------#

# functionName() : brief description [: 'GET', 'POST' ]
#
#
# viewMain() : home page
#
# viewGames() : a list of games
# viewGenres() : a list of genres : 'GET', POST'
# viewPublishers() : a list of publishers : 'GET', POST'
#
# viewGamePage() : view the page of a game : 'GET', POST'
# viewGenrePage() : view the page of a genre : 'GET', POST'
# viewPubPage() : view the page of a publisher: 'GET', POST'
# 
# editGame() : view/change the page of a game : 'GET', POST'
# editGenre() : view/change the page of a genre : 'GET', POST'
# editPublisher() : view/change the page of a publisher: 'GET', POST'
#
# newGame() : create a new game page : 'GET', POST'
# newGenre() : create a genre game page : 'GET', POST'
# newPublisher() : create a new publisher page: 'GET', POST'

@app.route('/')
@app.route('/main/')
def viewMain():
    """Takes the user to the home page.
    
    If the user is logged in, render the html template with the drop-down buttons.
    """
    picnumber = random.randint(1,2)
    game = session.query(Game.description).first()
    
    # renders public version of this page
    if 'username' not in login_session:
        return render_template('main.html', game=game, picnumber=picnumber)
        
    # renders private (user logged in) version of this page
    return render_template('main.html', game=game,
                            username = login_session['username'],
                            picnumber=picnumber)
    
@app.route('/main/games')
def viewGames():
    """Takes the user a page with a list of the games in the DB.
    
    If the user is logged in, render the html template with the drop-down buttons
    in the nav bar.
    """
    games = session.query(Game).order_by(Game.name).all()
    
    genre_names = listNames(Genre)
    pub_names = listNames(Publisher)
    
    # renders public version of this page
    if 'username' not in login_session:
        return render_template('view_games.html', games=games,
                                genre_names=genre_names,
                                pub_names=pub_names)
    
    # renders private version of this page
    return render_template('view_games.html', games=games,
                            genre_names=genre_names, pub_names=pub_names,
                            username = login_session['username'])


@app.route('/main/genres', methods=['GET', 'POST'])
def viewGenres():
    """Takes the user to a page with a list of the genres in the DB. GET and POST
    
    If the user is logged in, render a page with:
        Drop-down buttons in the nav-bar
        Edit and delete buttons for each publisher
    """
    genre_names = listNames(Genre) 
    
    # renders the public version of this page
    if 'username' not in login_session:
        return render_template('view_genres.html', genre_names=genre_names) 
        
    if request.method == 'POST':
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
            
        if checkAuthor(rqClean('name'), Genre): # checks if user is authorized to make changes
            return redirect('/main/'+Genre.__tablename__+'s')
            
        return handleDelete(rqClean('name'), Genre)

    return render_template('view_genres.html', genre_names=genre_names,
                            username = login_session['username'],
                            STATE = login_session['state'])

 
@app.route('/main/publishers', methods=['GET', 'POST'])
def viewPublishers():
    """Takes the user to a page with a list of the publishers in the DB. GET and POST
    
    If the user is logged in, render a page with:
        Drop-down buttons in the nav-bar
        Edit and delete buttons for each publisher
    """
    pub_names = listNames(Publisher)
    
    # renders the public persion of this page
    if 'username' not in login_session:
        return render_template('view_publishers.html', pub_names=pub_names)
        
    if request.method == 'POST':
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
            
        if checkAuthor(rqClean('name'), Publisher): # checks if user is authorized to make changes
            return redirect('/main/'+Publisher.__tablename__+'s')        
        
        return handleDelete(request.form['name'], Publisher)
        
    return render_template('view_publishers.html', pub_names=pub_names,
                            username = login_session['username'],
                            STATE = login_session['state'])                            
                            
@app.route('/main/games/<string:game_name>/', methods = ['GET', 'POST'])
def viewGamePage(game_name):
    """Takes the user to a game's page. GET and POST
    
    If the user is logged in, render a page with: 
        Drop-down buttons in the nav-bar
        Edit and delete buttons 
    """
    game = session.query(Game).filter(Game.name==game_name).one()

    if game.pic_url:
        pic_url = url_for('static', filename='pics/'+game.pic_url)
    else:
        pic_url = url_for('static', filename='pics/'+'placeholder.png')
    
    # renders public version of this page
    if 'username' not in login_session:
        return render_template('view_game.html', game=game, pic_url=pic_url)
     
    
    if request.method == 'POST':
        # the following line requests a token in order to procede with the
        # action of the post request. I'm not sure if this protects from CSRF
        # attacks
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
            
        if checkAuthor(game_name, Game):
            return redirect('/main/'+Game.__tablename__+'s/'+game_name)
            
        if request.form['button'] == 'Delete Game':
            name = game.name
            session.delete(game)
            session.commit()
            flash('"%s" was deleted.' % name)
            return redirect(url_for('viewGames'))
        
    return render_template('view_game.html', game=game, pic_url=pic_url,
                            username = login_session['username'],
                            STATE = login_session['state'])
    
@app.route('/main/genres/<string:genre_name>/', methods = ['GET', 'POST'])
def viewGenrePage(genre_name):
    """Takes the user to a genre's page. GET and POST
    
    If the user is logged in, render a page with:
        Drop-down buttons in the nav-bar
        Edit and delete buttons 
    """
    genre = session.query(Genre).filter(Genre.name==genre_name).one()
    games = session.query(Game).filter(Game.genre_name == genre_name).order_by(Game.name).all()
    
    # pub_names is provided for the JS manipulations of the game list that 
    # appears on a genre page
    pub_names = []
    for game in games:
        if game.publisher_name not in pub_names:
            pub_names.append(game.publisher_name)
            pub_names.sort()
    
    # if user is not logged in, render a page without a token and without certain buttons
    if 'username' not in login_session:
        return render_template('view_genre.html', genre=genre, games=games,
                                pub_names=pub_names)
    
    if request.method == 'POST':
        # prevents CSRF?
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'

        if checkAuthor(genre_name, Genre): # checks if user is authorized to make changes
            return redirect('/main/'+Genre.__tablename__+'s/'+genre_name)
            
        if request.form['button'] == 'Delete Genre':
            return handleDelete(genre.name, Genre)
    
    return render_template('view_genre.html', genre=genre, games=games,
                            pub_names=pub_names,
                            username = login_session['username'],
                            STATE = login_session['state'])

@app.route('/main/publishers/<string:pub_name>/', methods = ['GET', 'POST'])
def viewPubPage(pub_name):
    """Takes the user to a publisher's page. GET and POST
    
    If the user is logged in, render a page with:
        Drop-down buttons in the nav-bar
        Edit and delete buttons 
    """
    publisher = session.query(Publisher).filter(Publisher.name==pub_name).one()
    games = session.query(Game).filter(Game.publisher_name == pub_name).order_by(Game.name).all()
    
    # genre_names is provided for the JS manipulations of the game list that 
    # appears on a publisher page
    genre_names = []
    for game in games:
        if game.genre_name not in genre_names:
            genre_names.append(game.genre_name)
        genre_names.sort()
    
    # if user is not logged in, render a page without a token and without
    # delete and edit buttons
    if 'username' not in login_session:
        return render_template('view_publisher.html', publisher=publisher,
                                games=games,genre_names=genre_names)
        
    if request.method == 'POST':
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
            
        if checkAuthor(pub_name, Publisher): # checks if user is authorized to make changes
            return redirect('/main/'+Publisher.__tablename__+'s/'+pub_name)
            
        if request.form['button'] == 'Delete Publisher':
            return handleDelete(publisher.name, Publisher)
        
    return render_template('view_publisher.html', publisher=publisher,
                            games=games, genre_names=genre_names,
                            username = login_session['username'],
                            STATE = login_session['state'])
  
  
@app.route('/main/games/<string:game_name>/edit/', methods=['GET', 'POST'])
def editGame(game_name):
    """(GET) Takes the user to an edit-game page. (POST) Edits a game in the DB.

    Requirement: In order to view this page, the user must be logged in as the
    the page's creator OR as a 'superuser'.
    
    (GET)
    Render a page with:
        Drop-down buttons in the nav-bar.
        Text fields.
        Drop-down select bar.
        A file-upload button.
        'Save Changes' and 'Delete' buttons.
    
    (POST)
    Checks if game name already exists in DB.
        If it does exist, then stops the creation of new page by redirecting user
        to new-game page
    Checks if each field of the form has input.
        If a field has input, make a change to a database.
        If a field doesn't have input, add a preset value for the corresponding
        column of the game object.
    Adds a game to the DB.
    Returns user to Games page.
    """
    # prevents a user from accessing this page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')
  
    game = session.query(Game).filter(Game.name==game_name).one()
    
    if checkAuthor(game_name, Game): # checks if user is authorized to make changes
            return redirect('/main/'+Game.__tablename__+'s/'+game_name)
  
    if request.method == 'POST':
        # prevents CSRF ?
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
      
        if request.form['button'] == 'Delete Game':
            name = game.name
            session.delete(game)
            session.commit()
            flash('"%s" was deleted.' % name)
            return redirect(url_for('viewGames'))
    
        if request.files['game-image']:
            game.pic_url = uploadFile()
        
        name=rqClean('name')
        if name: # editing a game to duplicate its name
            if name in listNames(Game):
                flash('Name already taken! "%s" NOT created!' % name)
                return redirect('#')
            else:
                game.name=name
        if rqClean('genre') != game.genre_name:
            game.genre_name = rqClean('genre')
        if rqClean('publisher') != game.publisher_name:
            game.publisher_name = rqClean('publisher')
        if rqClean('rdate'):
            rd = rqClean('rdate').split('-')
            rd = datetime(int(rd[0]),int(rd[1]),int(rd[2]))
            game.release_date = rd
        if rqClean('market_value'):
            game.market_value = rqClean('market_value')
        if rqClean('mv_date'):
            md = rqClean('mv_date').split('-')
            md = datetime(int(md[0]),int(md[1]),int(md[2]))
            game.mv_date = md
        if rqClean('description'):
            game.description = rqClean('description')
        if rqClean('rating'):
            game.rating = rqClean('rating')
        
        # if there have been changes to a game, commit changes to DB
        if session.dirty:
            session.add(game)
            session.commit()
            flash('Game successfully edited.')
            return redirect(url_for('viewGamePage', game_name=game.name))
        else:
            flash('No changes saved.')
            return redirect(url_for('editGame', game_name=game_name))
    
    # these lists are used for the dropdown select menu    
    genre_names = listNames(Genre)
    pub_names = listNames(Publisher)
    
    if game.pic_url:
        pic_url = url_for('static', filename='pics/'+game.pic_url)
    else:
        pic_url = url_for('static', filename='pics/'+'placeholder.png')
    return render_template('edit_game.html', game=game, pic_url=pic_url,
                            pub_names=pub_names, genre_names=genre_names,
                            username = login_session['username'],
                            STATE = login_session['state'])



@app.route('/main/genres/<string:genre_name>/edit/', methods=['GET', 'POST'])
def editGenre(genre_name):
    """(GET) Takes the user to an edit-genre page. (POST) Edits a genre in the DB.

    Requirement: In order to view this page, the user must be logged in as the
    the page's creator OR as a 'superuser'.
    
    (GET)
    Render a page with:
        Drop-down buttons in the nav-bar.
        Text fields.
        'Save Changes' and 'Delete' buttons.
        A list of games related to this genre.
    
    (POST)
    Checks if genre name already exists in DB.
        If it does exist, then stops the creation of new page by redirecting user
        to new-genre page
    Checks if each field of the form has input.
        If a field has input, make a change to a database.
        If a field doesn't have input, add a preset value for the corresponding
        column of the genre object.
    Adds a genre to the DB.
    Returns user to Genres page.
    """
    
    # prevents a user from accessing this page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')
    
    genre = session.query(Genre).filter(Genre.name==genre_name).one()
    
    if checkAuthor(genre_name, Genre): # checks if user is authorized to make changes
            return redirect('/main/'+Genre.__tablename__+'s/'+genre_name)
    
    if request.method == 'POST':
        # prevents CSRF ?
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
        if request.form['button'] == 'Delete Genre':
            return handleDelete(genre.name, Genre)

        if request.form['button'] != 'Save Changes':
            return redirect(url_for('viewGenrePage', genre_name=genre_name))
        
        name = rqClean('name')
        if name:
            if name in listNames(Genre):
                flash('Name already taken! "%s" NOT created!' % name)
                return redirect('/main/newgenre')
            else:
                old_name = genre.name
                genre.name = name
        
        genre_descrip = rqClean('description')
        if genre_descrip:
            genre.description = genre_descrip
         
        if session.dirty:
            session.add(genre)
            session.commit()
            flash('Genre successfully edited.')
            
            # update game table to reflect name change
            if name:
                conn = engine.connect()
                stmt = text("UPDATE game "
                        "SET genre_name='%s' "
                        "WHERE genre_name='%s'" % (name, old_name))
                result = conn.execute(stmt)
                result.close()
            
            return redirect(url_for('viewGenrePage', genre_name=genre.name))
        else:
            flash('No changes saved.')
            return redirect(url_for('editGenre', genre_name=genre.name))
            
    games = session.query(Game).filter(Game.genre_name == genre_name).order_by(Game.name).all()    
    pub_names = []
    for game in games:
        if game.publisher_name not in pub_names:
            pub_names.append(game.publisher_name)
        pub_names.sort()

    return render_template('edit_genre.html', games=games, genre=genre,
                            pub_names=pub_names,
                            username = login_session['username'],
                            STATE = login_session['state'])


@app.route('/main/publishers/<string:pub_name>/edit/', methods=['GET', 'POST'])
def editPublisher(pub_name):
    """(GET) Takes the user to a edit-publisher page. (POST) Edits a publisher in the DB.

    Requirement: In order to view this page, the user must be logged in as the
    the page's creator OR as a 'superuser'.
    
    (GET)
    Render a page with:
        Drop-down buttons in the nav-bar.
        Text fields.
        'Save Changes' and 'Delete' buttons.
        A list of games produced by this publisher.
    
    (POST)
    Checks if publisher name already exists in DB.
        If it does exist, then stops the creation of new page by redirecting user
        to new-publisher page
    Checks if each field of the form has input.
        If a field has input, make a change to a database.
        If a field doesn't have input, add a preset value for the corresponding
        column of the publisher object.
    Adds a publisher to the DB.
    Returns user to Publishers page.
    """
    
    # prevents a user from accessing page if the user is not logged in.
    if 'username' not in login_session:
        return redirect('/login')
    
    publisher = session.query(Publisher).filter(Publisher.name==pub_name).one()
    
    if checkAuthor(pub_name, Publisher): # checks if user is authorized to make changes
        return redirect('/main/'+Publisher.__tablename__+'s/'+pub_name)
    
    if request.method == 'POST':
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
        if request.form['button'] == 'Delete Publisher':
            return handleDelete(publisher.name, Publisher)

        if request.form['button'] != 'Save Changes':
            return redirect(url_for('viewPubPage', pub_name=pub_name))
        
        name = rqClean('name')
        if name: # editing a publisher to duplicate its name
            if name in listNames(Publisher):
                flash('Name already taken! "%s" NOT created!' % name)
                return redirect('#')
            else:
                old_name = publisher.name
                publisher.name=name
        
        publisher_descrip = rqClean('description')
        if publisher_descrip:
            publisher.description = publisher_descrip
        
        # if there have been changes to a publisher, commit changes to DB
        if session.dirty:
            session.add(publisher)
            session.commit()
            flash('Publisher successfully edited.')
            
            # update game tables to reflect name change
            if name:
                conn = engine.connect()
                stmt = text("UPDATE game "
                        "SET publisher_name='%s' "
                        "WHERE publisher_name='%s'" % (name, old_name))
                result = conn.execute(stmt)
                result.close()
            
            return redirect(url_for('viewPubPage', pub_name=publisher.name))
        else:
            flash('No changes saved.')
            return redirect(url_for('editPublisher', pub_name=publisher.name))
         
    games = session.query(Game).filter(Game.publisher_name == pub_name).order_by(Game.name).all()
    genre_names = []
    for game in games:
        if game.genre_name not in genre_names:
            genre_names.append(game.genre_name)
        genre_names.sort()

    return render_template('edit_publisher.html', games=games,
                            publisher=publisher, genre_names=genre_names,
                            username = login_session['username'],
                            STATE = login_session['state'])


@app.route('/main/newgame', methods=['GET', 'POST'])
def newGame():
    """(GET) Takes the user to a new-game page. (POST) Enters a new game into the DB.

    Requirement: A user must be logged in to view this page.
    
    (GET)
    Render a page with:
        Drop-down buttons in the nav-bar.
        A 'Save Changes' button.
    
    (POST)
    Checks if game name already exists in DB.
        If it does exist, then stops the creation of new page by redirecting user
        to new-game page
    Checks if each field of the form has input.
        If a field has input, make a change to a database.
        If a field doesn't have input, add a preset value for the corresponding
        column of the game object.
    Adds a game to the DB.
    """
    if 'username' not in login_session:
        return redirect('/login')
        
    if request.method == 'POST':
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
        name, rating, genre_name, publisher_name = '', '', '', ''
        release_date, market_value, mv_date = None, '', None
        description = ''
        game_names = listNames(Game)
        
        # check if user sent request with blank field for game name
        # if yes, then interrupt request and redirect user to newgame page.
        if rqClean('name'):
            if rqClean('name') == '':
                flash('Game must have a name!')
                return redirect('/main/newgame')
            elif rqClean('name') in game_names:
                flash('Game name already taken! Game NOT created!')
                return redirect('/main/newgame')
            else:
                name = rqClean('name')
        if rqClean('genre'):
            genre_name = rqClean('genre')
        if rqClean('publisher'):
            publisher_name = rqClean('publisher')
        if rqClean('rdate'):
            rd = rqClean('rdate').split('-')
            release_date = datetime(int(rd[0]),int(rd[1]),int(rd[2]))
        if rqClean('market_value'):
            market_value = rqClean('market_value')
        if rqClean('mv_date'):
            md = rqClean('mv_date').split('-')
            mv_date = datetime(int(md[0]),int(md[1]),int(md[2]))
        if rqClean('description'):
            description = rqClean('description')
        if rqClean('rating'):
            rating = rqClean('rating')
        
        game = Game(name=name, genre_name=genre_name,
        publisher_name=publisher_name, release_date=release_date,
        market_value=market_value, mv_date=mv_date, description=description,
        rating=rating, user_email=login_session['email'])

        if request.files['game-image']:
            game.pic_url = uploadFile()
        session.add(game)
        session.commit()
        
        flash('"%s" successfully created!' % name)
        
        return redirect('/main/games')
        
        
    genre_names = listNames(Genre)
    pub_names = listNames(Publisher)
    return render_template('new_game.html', genre_names=genre_names,
                            pub_names=pub_names,
                            username = login_session['username'],
                            STATE = login_session['state'])                            
@app.route('/main/newgenre', methods=['GET', 'POST'])
def newGenre():
    """(GET) Takes the user to a new-genre page. (POST) Enters a new genre into the DB.

    Requirement: A user must be logged in to view this page.
    
    (GET)
    Render a page with:
        Drop-down buttons in the nav-bar.
        A 'Save Changes' button.
    
    (POST)
    Checks if genre name already exists in DB.
        If it does exist, then stops the creation of new page by redirecting user
        to new-genre page
    Checks if each field of the form has input.
        If a field has input, make a change to a database.
        If a field doesn't have input, add a preset value for the corresponding
        column of the genre object.
    Adds a genre to the DB.
    """
    # prevents an unauthenticated user from accessing this function
    if 'username' not in login_session:
        return redirect('/login')
    
    if request.method == 'POST':
        # prevents CSRF ?
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
        name = rqClean('name')
        if name:
            if name in listNames(Genre):
                flash('Name already taken! "%s" NOT created!' % name)
                return redirect('/main/newgenre')
        else:
            flash('Genre must have a name!')
            return redirect('/main/newgenre')
        
        description = rqClean('description')

        # if rqClean('description'):
        # description = rqClean('description')
        genre = Genre(name=name, user_email=login_session['email'],
                      description=description)
        session.add(genre)
        session.commit()
        flash('"%s" was successfully created!' % name)
        
        return redirect(url_for('viewGenres'))
            
    return render_template('new_genre.html',
                            username = login_session['username'],
                            STATE = login_session['state'])

@app.route('/main/newpublisher', methods=['GET', 'POST'])    
def newPublisher():
    """(GET) Takes the user to a new-publisher page. (POST) Enters a new publisher into the DB.

    Requirement: A user must be logged in to view this page.
    
    (GET)
    Render a page with:
        Drop-down buttons in the nav-bar.
        A 'Save Changes' button.
    
    (POST)
    Checks if publisher name already exists in DB.
        If it does exist, then stops the creation of new page by redirecting user
        to new-publisher page
    Checks if each field of the form has input.
        If a field has input, make a change to a database.
        If a field doesn't have input, add a preset value for the corresponding
        column of the publisher object.
    Adds a publisher to the DB.
    """
    # prevents an unauthenticated user from accessing this function
    if 'username' not in login_session:
        return redirect('/login') 

    if request.method == 'POST':
        # prevents CSRF ?
        if login_session['state'] != request.form['CSRFToken']:
            return 'hehehe'
        name = rqClean('name')
        if name:
            if name in listNames(Publisher):
                flash('Name already taken! "%s" NOT created!' % rqClean('name'))
                return redirect('/main/newpublisher')
        else:
            flash('Publisher must have a name!')
            return redirect('/main/newpublisher')
            
        description = rqClean('description')

        # if rqClean('description'):
        # description = rqClean('description')
        pub = Publisher(name=name, user_email=login_session['email'],
                        description=description)
        session.add(pub)
        session.commit()
        flash('"%s" was successfully created!' % name)
        
        return redirect(url_for('viewPublishers'))
    
    return render_template('new_publisher.html',
                            username = login_session['username'],
                            STATE = login_session['state'])
    

 
### BEGIN JSON ENDPOINTS

@app.route('/main/games/<string:game_name>/JSON')
def gameJSON(game_name):
    """Displays a game's information in JSON format."""
    game = session.query(Game).filter_by(name=game_name).one()
    return jsonify(game=game.serialize)

@app.route('/main/games/JSON')
def gamesJSON():
    """Displays the DB's games' information in JSON format."""
    games=session.query(Game).all()
    return jsonify(games=[r.serialize for r in games])
    
@app.route('/main/genres/JSON')
def genresJSON():
    """Displays the DB's genres' names and descriptions in JSON format."""
    genres=session.query(Genre).all()
    return jsonify(genres=[i.serialize for i in genres])

@app.route('/main/publishers/JSON')
def publishersJSON():
    """Displays the DB's publishers' names and descriptions in JSON format."""
    publishers=session.query(Genre).all()
    return jsonify(publishers=[i.serialize for i in publishers])    
    

### BEGIN XML Endpoints

def gameXMLHelper(games):
    """This is a helper function for gameXML and gamesXML.
    
    Arguments:
        games: a list containing Game objects.
    
    Returns:
        Returns an XML-formatted string carrying game(s) information.
    """
    games_list = [r.serialize for r in games]
    games_string=''
    for game_obj in games_list:
        # create xml elements and subelements
        game = ET.Element('game', attrib={'genre': game_obj['genre'],
                                          'publisher': game_obj['publisher']})
        name = ET.SubElement(game, 'name')
        description = ET.SubElement(game, 'description')
        release_date = ET.SubElement(game, 'release_date')
        rating = ET.SubElement(game, 'rating')
        market_value = ET.SubElement(game, 'market_value')
        mv_date = ET.SubElement(game, 'mv_date')
    
        # insert text into elements and subelements
        name.text = game_obj['name']
        description.text = game_obj['description']
        release_date.text = game_obj['release_date']
        rating.text = game_obj['rating']
        market_value.text = game_obj['market_value']
        mv_date.text = game_obj['mv_date']
        games_string+= ET.tostring(game, encoding='us-ascii', method='xml')
        
    return games_string

@app.route('/main/games/<string:game_name>/XML')
def gameXML(game_name):
    """Displays a game's information in XML format."""
    game = [session.query(Game).filter_by(name=game_name).one()]
    return gameXMLHelper(game)

@app.route('/main/games/XML')
def gamesXML():
    """Displays the DB's games' information in XML format."""
    games=session.query(Game).all()
    return gameXMLHelper(games)
    
@app.route('/main/genres/XML')
def genresXML():
    """Displays the DB's genres' names and descriptions in XML format."""
    genres=session.query(Genre).all()
    genres=[i.serialize for i in genres]
    
    genres_string=''
    for genre_obj in genres:
        # create xml elements and subelements
        genre = ET.Element('genre')
        name = ET.SubElement(genre, 'name')
        description = ET.SubElement(genre, 'description')
        
        # insert text into elements and subelements
        name.text = genre_obj['name']
        description.text = genre_obj['description']

        genres_string+= ET.tostring(genre, encoding='us-ascii', method='xml')
        
    return genres_string

@app.route('/main/publishers/XML')
def publishersXML():
    """Displays the DB's publishers' names and descriptions in XML format."""
    publishers=session.query(Publisher).all()
    publishers=[i.serialize for i in publishers]
    
    pub_string=''
    for pub_obj in publishers:
        # create xml elements and subelements
        pub = ET.Element('publisher')
        name = ET.SubElement(pub, 'name')
        description = ET.SubElement(pub, 'description')
        
        # insert text into elements and subelements
        name.text = pub_obj['name']
        description.text = pub_obj['description']

        pub_string+= ET.tostring(pub, encoding='us-ascii', method='xml')
        
    return pub_string
#END XML Endpoints
    
###  Helper Functions

def listNames(obj):
    """Fetches names from a specified Class/'table'
    
    Args:
        obj: a class name from icgb_database_setup.py, eg Game, User, etc
        
    Return:
        A list of names (strings).
    """
    names = session.query(obj.name).order_by(obj.name).all()
    for i in range(0, len(names)):
        names[i] = str(names[i][0])
    return names

def listSuperUsers():
    """ Return a list of 'superusers' from the DB """
    superusers = session.query(User.email).filter_by(privilege='superuser').all()
    for i in range(0,len(superusers)):
        superusers[i] = str(superusers[i][0])
    return superusers

def checkAuthor(obj_name, obj_class):
    """Determines if a user has the authority to make a change.
    
    Args:
        obj_name: name(string) of genre, publisher, or game to delete
        obj_class: Genre, Publisher, or Game
    
    Returns:
        Returns True if a user is NOT authorized to make a change. 
        Returns False if a user IS authorized to make a change.
    """
    toDeleteName = obj_name
    superUsers = listSuperUsers()
    
    creator_email = session.query(obj_class).filter(obj_class.name==toDeleteName).first().user_email
    print creator_email
    checkSuper = (login_session['email'] in superUsers) # if True, user IS authorized
    
    
    # checks authority of user to make a change
    if login_session['email'] == creator_email or checkSuper: 
        return False # user is authorized to make change
    flash('You are not the creator of this %s, you may not edit/delete it.' % obj_class.__tablename__)
    return True # user is NOT authorized to make change

    
def handleDelete(obj_name, obj_class):
    """Handles a delete request for genre pages and publisher pages. 
    
    Args:
        obj_name: name(string) of genre or publisher to delete
        obj_class: either Genre or Publisher
    
    Return:
        Carries out request and commits transaction to database. Redirects user
        to genre or publisher page.
    """
    toDeleteName = obj_name
    superUsers = listSuperUsers()
    
    # prevents 'Other' from being deleted.
    # 'Other' is important because when a genre/publisher is deleted, the
    # games with those genre/publishers are updated to have "Other" as their
    # genre/publisher
    if toDeleteName == 'Other':
        flash('You cannot delete "Other."')
        return redirect('/main/'+obj_class.__tablename__+'s/'+toDeleteName)    
    
    # The following code block updates the genre_name/publisher_name values of
    # the game object if these values no longer exist in the Genre/Publisher
    # tables. Values are updated to "other"
    t_name = obj_class.__tablename__
    conn = engine.connect()
    stmt = text("UPDATE game "
                "SET %s_name='%s' "
                "WHERE %s_name='%s'" % (t_name,'Other', t_name, toDeleteName))
    result = conn.execute(stmt)
    result.close()
            
    toDelete = session.query(obj_class).filter(obj_class.name==toDeleteName).all()[0]
    session.delete(toDelete)
    session.commit()
    flash('"%s" has been deleted.' % toDeleteName)
    return redirect('/main/'+obj_class.__tablename__+'s')
  
def rqClean(name):
    """Request and sanitize input from html forms."""
    return bleach.clean(request.form[name])
    
# Oauth Helper Functions
def createUser(email):
    """Creates a user in the DB with the user's email address.
    
    Argument:
        email: a string containing the email address of the new user.
        
    Return:
        Does not return anything. Commits transaction to the database.
    """
    newUser = User(name=login_session['username'], email=email)
    session.add(newUser)
    session.commit()
    #user = session.query(User).filter_by(email=login_session['email']).one()
    
def checkEmail(email):
    """Checks if the user email exists in the database."""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.email
    except:
        return None
    
    
if __name__=='__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)