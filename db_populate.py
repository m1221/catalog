from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from icgdb_database_setup import Base, Genre, Game, Publisher, User

engine = create_engine('sqlite:///icgdb.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# filler text
text_1 = 'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?'
text_2 ='At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus.'

# create superuser
superuser = User(name='Mario Portocarrero', email='m.portocarrero.jr@gmail.com', privilege='superuser')
session.add(superuser)
session.commit()

# Genres
genres = [['RTS',1, text_1], ['RPG',2, text_2], ['FPS',3, text_2],
          ['Sports',4, text_2], ['Turn-based',5,text_1], ['MMO',6,text_1],
          ['MOBA', 7, text_1], ['Horror',8, text_2], ['Other',0, text_2]]

# Add Genres
for genre in genres:
  newGenre = Genre(name=genre[0], id=genre[1], description=genre[2])
  session.add(newGenre)
  session.commit()

# Publishers
publishers = [
  {
    'id': 0,
    'name': 'Other',
    'description': text_1
  },
  {
    'id': 1,
    'name': 'Blizzard Entertainment',
    'description': text_2   
  },
  {
    'id': 2,
    'name': 'Sega',
    'description': text_1    
  },
  {
    'id': 3,
    'name': 'CD Projekt RED',
    'description': text_1    
  },
  {
    'id': 4,
    'name': 'Bethesda Softworks',
    'description': text_2    
  },
  {
    'id': 5,
    'name': 'Valve Corporation',
    'description': text_1    
  },
  {
    'id': 6,
    'name': 'Psyonix',
    'description': text_1    
  },
  {
    'id': 7,
    'name': '2k Games',
    'description': text_2    
  },
  {
    'id': 8,
    'name': 'CCP Games',
    'description': text_2    
  },
  {
    'id': 9,
    'name': 'Sony',
    'description': text_1   
  }  
]

# Add Publishers
for pub_info in publishers:
  newPublisher = Publisher(name=pub_info['name'], id=pub_info['id'], description=pub_info['description'])
  session.add(newPublisher)
  session.commit()
  
# Games
games = [
  {
    'name': 'StarCraft2: Wings of Liberty',
    'genre_id': 1,
    'release_date': '2010-07-27',
    'publisher_id': 1,
    'rating': '93/100',
    'description': text_1,
    'market_value': '$30',
    'mv_date': '2015-01-01',
    'pic_url': 'sc2wol.jpg'
  },
  {
    'name': 'StarCraft2: Heart of the Swarm',
    'genre_id': 1,
    'release_date': '2013-04-12',
    'publisher_id': 1,
    'rating': '86/100',
    'description': text_2,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'sc2hos.jpg'
  },
  {
    'name': 'Warhammer 40,000: Dawn of War',
    'genre_id': 1,
    'release_date': '2004-09-20',
    'publisher_id': 2,
    'rating': '86/100',
    'description': text_1,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'w40k.jpg'
  },
  {
    'name': 'The Witcher 3: Wild Hunt',
    'genre_id': 2,
    'release_date': '2015-05-19',
    'publisher_id': 3,
    'rating': '94/100',
    'description': text_2,
    'market_value': '$60',
    'mv_date': '2015-01-01',
    'pic_url': 'witcher3.jpg'
  },
  {
    'name': 'The Elder Scrolls V: Skyrim',
    'genre_id': 2,
    'release_date': '2013-04-12',
    'publisher_id': 4,
    'rating': '94/100',
    'description': text_2,
    'market_value': '$30',
    'mv_date': '2015-01-01',
    'pic_url': 'skyrim.jpg'
  },
  {
    'name': 'Counter-Strike: Global Offensive',
    'genre_id': 3,
    'release_date': '2012-08-21',
    'publisher_id': 5,
    'rating': '83/100',
    'description': text_1,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'csgo.jpg'
  },
  {
    'name': 'Left 4 Dead 2',
    'genre_id': 3,
    'release_date': '2009-11-17',
    'publisher_id': 5,
    'rating': '89/100',
    'description': text_1,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'l4d2.jpg'
  },
  {
    'name': 'Rocket League',
    'genre_id': 4,
    'release_date': '2015-07-07',
    'publisher_id': 6,
    'rating': '86/100',
    'description': text_2,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'rleague.jpg'
  },
  {
    'name': 'Football Manager 2015',
    'genre_id': 4,
    'release_date': '2013-04-12',
    'publisher_id': 2,
    'rating': '86/100',
    'description': text_2,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'fbmanager.jpg'
  },
  {
    'name': 'Civilization V',
    'genre_id': 5,
    'release_date': '2010-09-21',
    'publisher_id': 7,
    'rating': '90/100',
    'description': text_1,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'civ5.jpg'
  },
  {
    'name': 'Eve Online: Apocrypha',
    'genre_id': 6,
    'release_date': '2003-05-06',
    'publisher_id': 8,
    'rating': '89/100',
    'description': text_2,
    'market_value': 'free',
    'mv_date': '2015-01-01',
    'pic_url': 'eve.jpg'
  },
  {
    'name': 'Dota 2',
    'genre_id': 7,
    'release_date': '2013-07-12',
    'publisher_id': 5,
    'rating': '90/100',
    'description': text_1,
    'market_value': 'free',
    'mv_date': '2015-01-01',
    'pic_url': 'dota2.jpg'
  },
  {
    'name': 'Until Dawn',
    'genre_id': 8,
    'release_date': '2015-08-25',
    'publisher_id': 9,
    'rating': '79/100',
    'description': text_2,
    'market_value': '$20',
    'mv_date': '2015-01-01',
    'pic_url': 'untildawn.jpg'
  }
  
]

# Add Games
for game in games:
  rd = game['release_date'].split('-')
  rd = datetime(int(rd[0]),int(rd[1]),int(rd[2]))
  md = game['mv_date'].split('-')
  md = datetime(int(md[0]),int(md[1]),int(md[2]))
  
  for x in genres:
    if x[1]==game['genre_id']:
      genre_name=x[0]
      break
  
  for y in publishers:
    if y['id']==game['publisher_id']:
      publisher_name=y['name']
      break

  newGame = Game(name=game['name'],
    genre_name=genre_name,
    release_date=rd,
    publisher_name=publisher_name,
    rating=game['rating'],
    description=game['description'],
    market_value=game['market_value'],
    mv_date=md,
    pic_url=game['pic_url'])
  session.add(newGame)
  session.commit()

  
print 'Reached end of file! Database successfully populated!'