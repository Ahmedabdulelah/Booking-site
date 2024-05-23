#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import sys
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging    
from logging import  FileHandler
from flask_wtf import Form,FlaskForm
from wtforms import StringField 
from forms import *
from models import *
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from config import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    
with app.app_context():
  db.create_all()


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    try:
        date = dateutil.parser.parse(str(value))
    except dateutil.parser.ParserError:
        return '' 
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    elif format == 'custom':
        format = "yyyy-MM-dd HH:mm:ss"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime



#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

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
      'num_upcoming_shows': len(list(filter(lambda x:x.start_time > datetime.today() , venue.shows_venues)))
    }
    if venue.city ==prev_city and venue.state ==prev_state:
      tmp['venues'].append(venue_data)
    else:
      if prev_city is None:
        data.append(tmp)
      tmp['city'] = venue.city
      tmp['state'] = venue.state
      tmp['venues'] = [venue_data]
    prev_city = venue.city
    prev_state = venue.state

  data.append(tmp)
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data = []

  for venue in venues:
    tmp = {}
    tmp['id'] = venue.id
    tmp['name'] = venue.name
    tmp['num_upcoming_shows'] = len(venue.shows_venues)
    data.append(tmp)

  response = {}
  response['count'] = len(data)
  response['data'] = data  

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  artist_id = Show.artist_id
  past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all() 

  past_show = list(map(lambda x: x.artist_relation , past_shows))
  upcoming_show = list(map(lambda x:x.artist_relation , upcoming_shows))

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
  form = VenueForm(request.form,meta = {'csrf':False})
  if form.validate():
    try:
      venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      phone = form.phone.data,
      genres = form.genres.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website = form.website.data,
      seeking_talent = form.seeking_talent.data,
      seeking_description = form.seeking_description.data,
      )
      db.session.add(venue)
      db.session.commit()
    except ValueError as e:
      print(f"error: {e}")
      error_info = sys.exc_info()
      print(f"Error Info: {error_info}")
      db.session.rollback()
    finally:
      db.session.close()  
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
      message = []
      for field, errors in form.errors.items():
        for error in errors:
          message.append(f"{field}: {error}")
      flash('Please fix the following errors: ' + ', '.join(message))
      form = VenueForm()
      return render_template('forms/new_venue.html', form=form)


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
  search_results = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  response = {}
  response ['count'] = len(search_results)
  response ['data'] = search_results
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  past_shows = list(filter(lambda x:x.start_time < datetime.today(),artist.shows_artists))
  upcoming_shows = list(filter(lambda x:x.start_time >= datetime.today(),artist.shows_artists))

  past_shows = list(map(lambda x:x.venue_relation , past_shows))
  upcoming_shows = list(map(lambda x:x.venue_relation ,upcoming_shows))

  data = artist.to_dict()
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
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)
  error = False
  try:
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.website = form.website.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error:
      flash('An error occurred. Artsit ' + artist.name + ' could not be updated')
    else:
      return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id).to_dict()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  error = False
  try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.image_link = form.image_link.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error:
      flash('An error occurred. Venue ' + venue.name + ' could not be updated')
    else:
      flash('Venue ' + venue.name + ' was successfully updated')  

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, meta = {'csrf':False})
  if form.validate():
    try:
      artist = Artist(
        name = form.name.data,
        state = form.state.data,
        city = form.city.data,
        phone = form.phone.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        website = form.website.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(artist)
      db.session.commit()
    except ValueError as e:
      print(f"Error:{e}")  
      error_info = sys_exc_info()
      print(f"Error Info :{error_info}")
      db.session.rollback()
    finally:
      db.session.close()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')  
    return render_template('pages/home.html')
  else:
    message = []
    for field, errors in form.errors.items():
        for error in errors:
            message.append(f"{field}: {error}")
    flash('Please fix the following errors: ' + ', '.join(message))
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

  return render_template('pages/home.html')


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    if artist is None:
      flash('Artist not found!')
      return redirect(url_for('index'))
    else:
      db.session.delete(artist)
      db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error:
      flash('An error occurred. Artsit could not be deleted')
    else:
      flash('Artist successfully deleted')
    return redirect(url_for('index'))        


@app.route('/artists/<int:artist_id>/delete',methods=['POST'])
def delete_artists(artist_id):
  artist = Artist.query.get(artist_id)
  if artist:
    db.session.delete(artist)
    db.session.commit()
    flash('Artist deleted successfuly','success')
  else:
    flash('Artist not found','error')
    return redirect(url_for('index'))  

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for show in shows:
    data.append({
      'venue_id' :show.venue_id,
      'venue_name':show.venue_name,
      'artist_id':show.artist_id,
      'artist_name':show.artist_name,
      'artist_image_link':show.artist_image_link,
      'start_time':show.start_time.isoformat()
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
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
