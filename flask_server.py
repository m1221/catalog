import os
from datetime import datetime
from werkzeug import secure_filename # for file upload
from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from icgdb_database_setup import Base, Game, Publisher, Genre, User

# oauth imports
import random, string
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, Credentials
import oauth2client.client
import httplib2
import json
import requests

# security import
import bleach

# XML endpoint import
import xml.etree.ElementTree as ET

# END IMPORTS

# oauth setup #
CLIENT_ID = json.loads(
  open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'ICGDB'

# Connect to db
engine = create_engine('sqlite:///icgdb.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# for file_upload_setup #
UPLOAD_FOLDER = os.path.abspath('static/pics')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024

def checkExtension(filename):
  return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# need to tailer for use inside other func  
def uploadFile():
  file = request.files['game-image']
  if file and checkExtension(file.filename):
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename

# OAUTH SETUP
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
    response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
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
    response = make_response(json.dumps("Token's client ID does not match the app's client ID."), 401)
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
    response = make_response(json.dumps('Current user not connected.'), 401)
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
    response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
    response.headers['Content-Type'] = 'application/json'
    return response
  
# END OAUTH SETUP #

# Begin page routing
@app.route('/')
@app.route('/main/')
def viewMain():
  picnumber = random.randint(1,2)
  game = session.query(Game.description).first()
  if 'username' not in login_session:
    return render_template('main.html', game=game, picnumber=picnumber)
  return render_template('main.html', game=game, username = login_session['username'], picnumber=picnumber)
  
@app.route('/main/games')
def viewGames():
  games = session.query(Game).order_by(Game.name).all()
  
  genre_names = listNames(Genre)
  pub_names = listNames(Publisher)
    
  if 'username' not in login_session:
    return render_template('view_games.html', games=games, genre_names=genre_names, pub_names=pub_names)
    
  return render_template('view_games.html', games=games, genre_names=genre_names, pub_names=pub_names, username = login_session['username'])

@app.route('/main/games/<string:game_name>/', methods = ['GET', 'POST'])
def viewGamePage(game_name):
  game = session.query(Game).filter(Game.name==game_name).one()

  if game.pic_url:
    pic_url = url_for('static', filename='pics/'+game.pic_url)
  else:
    pic_url = url_for('static', filename='pics/'+'placeholder.png')
    
  if 'username' not in login_session:
    return render_template('view_game.html', game=game, pic_url=pic_url)
   
  
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    superUsers = listSuperUsers()
    if login_session['email'] != str(game.user_email) and login_session['email'] not in superUsers:
      flash('You are not the creator of this game page. You shall NOT edit it.')
      return redirect(url_for('viewGamePage', game_name=game_name))
      
    if request.form['button'] == 'Delete Game':
      name = game.name
      session.delete(game)
      session.commit()
      flash('"%s" was deleted.' % name)
      return redirect(url_for('viewGames'))
    
  return render_template('view_game.html', game=game, pic_url=pic_url, username = login_session['username'], STATE = login_session['state'])
  
@app.route('/main/genres/<string:genre_name>/', methods = ['GET', 'POST'])
def viewGenrePage(genre_name):
 
  genre = session.query(Genre).filter(Genre.name==genre_name).one()
  games = session.query(Game).filter(Game.genre_name == genre_name).order_by(Game.name).all()
  pub_names = []
  for game in games:
    if game.publisher_name not in pub_names:
      pub_names.append(game.publisher_name)
    pub_names.sort()
    
  if 'username' not in login_session:
    return render_template('view_genre.html', genre=genre, games=games, pub_names=pub_names)
  
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'   
    if request.form['button'] == 'Delete Genre':
      return handleDelete(genre.name, Genre)
    
  return render_template('view_genre.html', genre=genre, games=games, pub_names=pub_names, username = login_session['username'], STATE = login_session['state'])  

@app.route('/main/publishers/<string:pub_name>/', methods = ['GET', 'POST'])
def viewPubPage(pub_name):

  publisher = session.query(Publisher).filter(Publisher.name==pub_name).one()
  games = session.query(Game).filter(Game.publisher_name == pub_name).order_by(Game.name).all()
  genre_names = []
  for game in games:
    if game.genre_name not in genre_names:
      genre_names.append(game.genre_name)
    genre_names.sort()
 
  if 'username' not in login_session:
    return render_template('view_publisher.html', publisher=publisher, games=games,genre_names=genre_names)
    
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    if request.form['button'] == 'Delete Publisher':
      return handleDelete(publisher.name, Publisher)
    
  return render_template('view_publisher.html', publisher=publisher, games=games, genre_names=genre_names, username = login_session['username'], STATE = login_session['state'])   
  
@app.route('/main/genres', methods=['GET', 'POST'])  
def viewGenres():
  genre_names = listNames(Genre) 
  
  if 'username' not in login_session:
    return render_template('view_genres.html', genre_names=genre_names) 
    
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    return handleDelete(rqClean('name'), Genre)

  return render_template('view_genres.html', genre_names=genre_names, username = login_session['username'], STATE = login_session['state'])

@app.route('/main/publishers', methods=['GET', 'POST'])
def viewPublishers():
  pub_names = listNames(Publisher)
    
  if 'username' not in login_session:
    return render_template('view_publishers.html', pub_names=pub_names)
    
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    return handleDelete(request.form['name'], Publisher)
    
  return render_template('view_publishers.html', pub_names=pub_names, username = login_session['username'], STATE = login_session['state'])  
  
@app.route('/main/games/<string:game_name>/edit/', methods=['GET', 'POST'])
def editGame(game_name):
  if 'username' not in login_session:
    return redirect('/login')
  
  game = session.query(Game).filter(Game.name==game_name).one()
  superUsers = listSuperUsers()
  
  if login_session['email'] != str(game.user_email) and login_session['email'] not in superUsers:
    flash('You are not the creator of this game page. You shall NOT edit it.')
    return redirect(url_for('viewGamePage', game_name=game_name))
  
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    if login_session['email'] != str(game.user_email) and login_session['email'] not in superUsers:
      flash('You are not the creator of this game page. You shall NOT edit it.')
      return redirect(url_for('viewGamePage', game_name=game_name))
      
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
    
    if session.dirty:
      session.add(game)
      session.commit()
      flash('Game successfully edited.')
      return redirect(url_for('viewGamePage', game_name=game.name))
    else:
      flash('No changes saved.')
      return redirect(url_for('editGame', game_name=game_name))
     
  genre_names = listNames(Genre)
  pub_names = listNames(Publisher)
  
  if game.pic_url:
    pic_url = url_for('static', filename='pics/'+game.pic_url)
  else:
    pic_url = url_for('static', filename='pics/'+'placeholder.png')
  return render_template('edit_game.html', game=game, pic_url=pic_url, pub_names=pub_names, genre_names=genre_names, username = login_session['username'], STATE = login_session['state'])

@app.route('/main/publisher/<string:pub_name>/edit/', methods=['GET', 'POST'])
def editPublisher(pub_name):
  if 'username' not in login_session:
    return redirect('/login')
  
  publisher = session.query(Publisher).filter(Publisher.name==pub_name).one()
  superUsers = listSuperUsers()
  if login_session['email'] != str(publisher.user_email) and login_session['email'] not in superUsers:
    flash('You are not the creator of this publisher page. You shall NOT edit it.')
    return redirect(url_for('viewPubPage', pub_name=pub_name))
      
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
        publisher.name=name
    
    publisher_descrip = rqClean('description')
    if publisher_descrip:
      publisher.description = publisher_descrip
    
    
    if session.dirty:
      session.add(publisher)
      session.commit()
      flash('Publisher successfully edited.')
      return redirect(url_for('editPublisher', pub_name=publisher.name))
    else:
      flash('No changes saved.')
      return redirect(url_for('editPublisher', pub_name=publisher.name))
     
  games = session.query(Game).filter(Game.publisher_name == pub_name).order_by(Game.name).all()
  genre_names = []
  for game in games:
    if game.genre_name not in genre_names:
      genre_names.append(game.genre_name)
    genre_names.sort()

  return render_template('edit_publisher.html', games=games, publisher=publisher, genre_names=genre_names, username = login_session['username'], STATE = login_session['state'])

@app.route('/main/genres/<string:genre_name>/edit/', methods=['GET', 'POST'])
def editGenre(genre_name):
  if 'username' not in login_session:
    return redirect('/login')
  
  genre = session.query(Genre).filter(Genre.name==genre_name).one()
  superUsers = listSuperUsers()
  if login_session['email'] != str(genre.user_email) and login_session['email'] not in superUsers:
    flash('You are not the creator of this genre page. You shall NOT edit it.')
    return redirect(url_for('viewGenrePage', genre_name=genre_name))
  
  if request.method == 'POST':
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
        genre.name = name
    
    genre_descrip = rqClean('description')
    if genre_descrip:
      genre.description = genre_descrip
    
    
    if session.dirty:
      session.add(genre)
      session.commit()
      flash('Genre successfully edited.')
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

  return render_template('edit_genre.html', games=games, genre=genre, pub_names=pub_names, username = login_session['username'], STATE = login_session['state'])
  
@app.route('/main/newgenre', methods=['GET', 'POST'])
def newGenre():
  if 'username' not in login_session:
    return redirect('/login')
  
  if request.method == 'POST':
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
    genre = Genre(name=name, user_email=login_session['email'], description=description)
    session.add(genre)
    session.commit()
    flash('"%s" was successfully created!' % name)
    
    return redirect(url_for('viewGenres'))
      
  return render_template('new_genre.html', username = login_session['username'], STATE = login_session['state'])

@app.route('/main/newpublisher', methods=['GET', 'POST'])  
def newPublisher():
  if 'username' not in login_session:
    return redirect('/login') 

  if request.method == 'POST':
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
    pub = Publisher(name=name, user_email=login_session['email'], description=description)
    session.add(pub)
    session.commit()
    flash('"%s" was successfully created!' % name)
    
    return redirect(url_for('viewPublishers'))
  
  return render_template('new_publisher.html', username = login_session['username'], STATE = login_session['state'])
  
@app.route('/main/newgame', methods=['GET', 'POST'])
def newGame():
  if 'username' not in login_session:
    return redirect('/login')
    
  if request.method == 'POST':
    if login_session['state'] != request.form['CSRFToken']:
      return 'hehehe'
    name, rating, genre_name, publisher_name, release_date, market_value, mv_date, description = '','','','', None,'', None,''
    game_names = listNames(Game)
    
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
    
    game = Game(name=name, genre_name=genre_name, publisher_name=publisher_name,
    release_date=release_date, market_value=market_value, mv_date=mv_date,
    description=description, rating=rating, user_email=login_session['email'])

    if request.files['game-image']:
      game.pic_url = uploadFile()
    session.add(game)
    session.commit()
    
    flash('"%s" successfully created!' % name)
    
    return redirect('/main/games')
    
    
  genre_names = listNames(Genre)
  pub_names = listNames(Publisher)
  return render_template('new_game.html', genre_names=genre_names, pub_names=pub_names, username = login_session['username'], STATE = login_session['state'])
  
#JSON Endpoints
@app.route('/main/games/<string:game_name>/JSON')
def gameJSON(game_name):
  game = session.query(Game).filter_by(name=game_name).one()
  return jsonify(game=game.serialize)

@app.route('/main/games/JSON')
def gamesJSON():
  games=session.query(Game).all()
  return jsonify(games=[r.serialize for r in games])
  
@app.route('/main/genres/JSON')
def genresJSON():
  genres=session.query(Genre).all()
  return jsonify(genres=[i.serialize for i in genres])

@app.route('/main/publishers/JSON')
def publishersJSON():
  publishers=session.query(Genre).all()
  return jsonify(publishers=[i.serialize for i in publishers])  
  
#END JSON Endpoints

#XML Endpoints
@app.route('/main/games/<string:game_name>/XML')
def gameXML(game_name):
  game = session.query(Game).filter_by(name=game_name).one()
  game_obj = game.serialize
  
  game = ET.Element('game', attrib={'genre': game_obj['genre'], 'publisher': game_obj['publisher']})
  name = ET.SubElement(game, 'name')
  description = ET.SubElement(game, 'description')
  release_date = ET.SubElement(game, 'release_date')
  rating = ET.SubElement(game, 'rating')
  market_value = ET.SubElement(game, 'market_value')
  mv_date = ET.SubElement(game, 'mv_date')
  
  name.text = game_obj['name']
  description.text = game_obj['description']
  release_date.text = game_obj['release_date']
  rating.text = game_obj['rating']
  market_value.text = game_obj['market_value']
  mv_date.text = game_obj['mv_date']
  
  #return app.response_class(ET.dump(game), mimetype='application/xml')
  #return str(ET.tostringlist(game, encoding="us-ascii", method="xml" ))
  return ET.tostring(game, encoding="us-ascii", method="xml" )

@app.route('/main/games/XML')
def gamesXML():
  games=session.query(Game).all()
  games=[r.serialize for r in games]
  
  games_string=''
  for game_obj in games:
    game = ET.Element('game', attrib={'genre': game_obj['genre'], 'publisher': game_obj['publisher']})
    name = ET.SubElement(game, 'name')
    description = ET.SubElement(game, 'description')
    release_date = ET.SubElement(game, 'release_date')
    rating = ET.SubElement(game, 'rating')
    market_value = ET.SubElement(game, 'market_value')
    mv_date = ET.SubElement(game, 'mv_date')
  
    name.text = game_obj['name']
    description.text = game_obj['description']
    release_date.text = game_obj['release_date']
    rating.text = game_obj['rating']
    market_value.text = game_obj['market_value']
    mv_date.text = game_obj['mv_date']
    games_string+= ET.tostring(game, encoding='us-ascii', method='xml')
    
  return games_string
  
@app.route('/main/genres/XML')
def genresXML():
  genres=session.query(Genre).all()
  genres=[i.serialize for i in genres]
  
  genres_string=''
  for genre_obj in genres:
    genre = ET.Element('genre')
    name = ET.SubElement(genre, 'name')
    description = ET.SubElement(genre, 'description')
  
    name.text = genre_obj['name']
    description.text = genre_obj['description']

    genres_string+= ET.tostring(genre, encoding='us-ascii', method='xml')
    
  return genres_string

@app.route('/main/publishers/XML')
def publishersXML():
  publishers=session.query(Publisher).all()
  publishers=[i.serialize for i in publishers]
  
  pub_string=''
  for pub_obj in publishers:
    pub = ET.Element('publisher')
    name = ET.SubElement(pub, 'name')
    description = ET.SubElement(pub, 'description')
  
    name.text = pub_obj['name']
    description.text = pub_obj['description']

    pub_string+= ET.tostring(pub, encoding='us-ascii', method='xml')
    
  return pub_string
#END XML Endpoints
  
# Helper Functions
def listNames(obj):
  names = session.query(obj.name).order_by(obj.name).all()
  for i in range(0, len(names)):
    names[i] = str(names[i][0])
  return names

def listSuperUsers():
  superusers = session.query(User.email).filter_by(privilege='superuser').all()
  for i in range(0,len(superusers)):
    superusers[i] = str(superusers[i][0])
  return superusers
  
def handleDelete(response, obj):
  toDeleteName = response
  superUsers = listSuperUsers()

  if toDeleteName == 'Other':
    flash('You cannot delete "Other."')
    return redirect('/main/'+obj.__tablename__+'s/'+toDeleteName)
    
  email = session.query(obj).filter(obj.user_email==login_session['email']).first()
  if login_session['email'] != str(email) and login_session['email'] not in superUsers:
    flash('You are not the creator of this %s, you may not delete it.' % obj.__tablename__)
    return redirect('/main/'+obj.__tablename__+'s/'+toDeleteName)

  if obj.__tablename__ == 'publisher':
    games = session.query(Game).filter(Game.publisher_name==toDeleteName).all()
    for game in games:
      game.publisher_name = "Other"
      session.add(game)
      session.commit()
  elif obj.__tablename__ == 'genre':
    games = session.query(Game).filter(Game.genre_name==toDeleteName).all()
    for game in games:
      game.genre_name = "Other"
      session.add(game)
      session.commit()
      
  toDelete = session.query(obj).filter(obj.name==toDeleteName).all()[0]
  session.delete(toDelete)
  session.commit()
  flash('"%s" has been deleted.' % toDeleteName)
  return redirect('/main/'+obj.__tablename__+'s')
  
def rqClean(name):
  return bleach.clean(request.form[name])
  
# oauth Helper Functions
def createUser(email):
  newUser = User(name=login_session['username'], email=email)
  session.add(newUser)
  session.commit()
  #user = session.query(User).filter_by(email=login_session['email']).one()
  
def checkEmail(email):
  try:
    user = session.query(User).filter_by(email=email).one()
    return user.email
  except:
    return None
  
  
if __name__=='__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)