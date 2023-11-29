#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
# import dateutil.parser
# import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import sys
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form,FlaskForm
from wtforms import StringField 
from forms import *
from sqlalchemy.exc import SQLAlchemyError
import psycopg2

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app , db)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:localdb@localhost:5432/booksite'

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean,default = False)
    seeking_description = db.Column(db.String(120))


    artists = db.relationship('Artist' , secondary = 'shows')
    show_relation = db.relationship('Show', backref=('venues'))
    


    def __repr__(self):
      return f"<Information Venue {self.id} {self.name}>"



class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))

    venues = db.relationship('Venue' , secondary = 'shows')
    show_relation = db.relationship('Show' , backref = ('artists'))

    def __repr__(self):
      return F"<Information Artist {self.id} {self.name} {self.genres}>"


class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer ,primary_key = True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"))
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"))
    start_time = db.Column(db.DateTime())

    venue_relation = db.relationship('Venue')
    artist_relation = db.relationship('Artist')

  
with app.app_context():
  db.create_all()


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by(Venue.state , Venue.city)
  data = []
  tmp = {}
  prev_city = None
  prev_state = None
  
  for venue in venues:
    venue_data = {
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': len(list(filter(lambda x:x.start_time > datetime.today() , venue.shows)))
    }
    if venue.city ==prev_city and venue.state ==prev_state:
      tmp['venues'].append(venue_data)
    else:
      if prev_city is none:
        data.append(tmp)
      tmp['city'] = venue.city
      tmp['state'] = venue.state
      tmp['venues'] = [venue_data]
    prev_city = venue.city
    prev_state = venue.state

  data.append(tmp)
  return render_template('pages/venues.html', area = data)       

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format('search_term'))).all()
  data = []

  for venue in venues:
    tmp = {}
    tmp['id'] = venue.id
    tmp['name'] = venue.name
    tmp['num_upcoming_shows'] = len(venue.shows)
    data.append(tmp)

  response = {}
  response['count'] = len(data)
  response['data'] = data  

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  past_show = list(filter(lambda x: x.start_time < datetime.today() , venue.shows))
  upcoming_show = list(filter(lambda x: x.start_time >= datetime.today() , venue.shows))

  past_show = list(map(lambda x: x.show_artist() , past_shows))
  upcoming_show = list(map(lambda x:x.show_artist() , upcoming_show))

  data = venue.to_dict()
  data['past_show'] = past_show
  data['upcoming_show'] = upcoming_show
  data['past_show_count'] = len(past_show)
  data['upcoming_show_count'] = len(upcoming_show)

  return render_template('pages/show_venue.html', venue=data)

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  venue = None
  try:
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    tmp_genres = request.form.getlist('genres')
    venue.genres = ','.join(tmp_genres)
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link'] 
    venue.website = request.form['website']
    venue.seeking_talent =bool(request.form['seeking_talent'])
    # venue.seeking_talent = request.form['seeking_talent']
    # venue.seeking_talent = True if request.form['seeking_talent'] == 'True' else False
    venue.seeking_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
  except Exception as e: 
    error = True
    db.session.rollback()
    print(e)
  finally:
    db.session.close()
    if error :
      flash('An error occurred. Venue ' + (venue.name if venue else '') + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    if venue is None:
      flash('Venue not found!')
      return redirect(url_for('index'))
    db.session.delete(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue could not be deleted!')
    else:
      flash('Venue successfully deleted')
    return redirect(url_for('index'))    
  return None

  
@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venues(venue_id):

  venue = Venue.query.get(venue_id)
  if venue:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue deleted successfully', 'success')
  else:
    flash('Venue not found', 'error')
  return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  search_results = Artist.query.format(Artist.name.ilike('%{}%'.format(search_term))).all()
  response = {}
  response ['count'] = len(search_results)
  response ['data'] = search_results

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  past_shows = list(filter(lambda x:x.start_time <datetime.today(),artist.shows))
  upcoming_shows = list(filter(lambda x:x.start_time >= datetime.today(),artist.shows))
  past_shows = list(map(lambda x:x.show_venue() , past_shows))
  upcoming_shows = list(map(lambda x:x.show_venue(),upcoming_shows))

  data = artist.to_dict()
  print(data)
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_show'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    tmp_genres = request.form.getlist(genres)
    artist.genres = ','.join(tmp_genres)
    artist.website = request.form['website']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.seeking_venue = request.form['seeking_venue']
    artist.seeking_description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      return redirect(url_for('server_error'))
    else:
      return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id).to_dict()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  error = False
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    tmp_genres = request.form.getlist(genres)
    venue.genres = ','.join(tmp_genres)
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = request.form['seeking_talent']
    venue.seeking_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close
    if error:
      flash('An error occurred. venue' + request.form['name'] + 'could not be updating')
    else:
      flash('Venue' + request.form['name'] + 'was successfuly updated')  

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  error = False
  try:
    artist = Artist()
    artist.name = request.form['name']
    artist.state = request.form['state']
    artist.city = request.form['city']
    artist.address = request.form['address']
    artist.phone = request.form = ['phone']
    tmp_genres = request.form.getlist('genres')
    artist.genres = ','.join(tmp_genres)
    artist.facebook_link = request.form['facebook_link'] 
    artist.website = request.form['website']
    artist.seeking_venue = request.form['seeking_venue']
    artist.seeling_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info()) 

  finally:
    db.session.close()
    if error:
      flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for show in shows:
    data.append({
      'venue_id' :show.venue.id,
      'venue_name':show.venue.name,
      'artist_id':show.artist.id,
      'artist_name':show.artist.name,
      'artist_image_link':show.artist.image_link,
      'start_time':show.start_time.isoformat()
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    show = Show()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time = request.form['start_time']
    db.session.add(show)
    db.session.commit()
  except SQLAlchemyError as e:
    error = True
    db.session.rollback()
    print(str(e))
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Show could not be listed.')
    else:
      flash('Show was successfully listed!')  

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
