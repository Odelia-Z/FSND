#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

import sys
from flask_migrate import Migrate
from datetime import date
from sqlalchemy import ForeignKey
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String())
    seeking_talent = db.Column(db.String())
    seeking_description = db.Column(db.String())
    
    show = db.relationship('Show', backref = 'venue')

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String())
    seeking_talent = db.Column(db.String())
    seeking_description = db.Column(db.String())
    
    show = db.relationship('Show', backref = 'Artist')

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key = True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)
    start_time = db.Column(db.DateTime, nullable = False)

    def __repr__(self):
       return f'<Show ID: {self.id}>'

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
  data = []
  # get all venue areas
  areas = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  for area in areas:
    app.logger.warning(area.city)
    area_venues = db.session.query(Venue).filter(Venue.city == area.city).all()
    venues = []
    for venue in area_venues:
      shows = db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
      v = {
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(shows)
      }
      venues.append(v)
    x = {
      'city': area.city,
      'state': area.state,
      'venues': venues
    }
    data.append(x)
  return render_template('pages/venues.html', areas=data);



@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = db.session.query(Venue).filter(Venue.name.ilike(f"%{search_term}%")).all()
  data = []
  for venue in venues:
      shows = db.session.query(Show).filter(Show.artist_id == venue.id).filter(Show.start_time > datetime.now()).all()
      x = {
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(shows)
      }
      data.append(x)
  
  response = {
      "count": len(venues),
      "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()

  if venue is None:
    return render_template('errors/404/html')

  shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).all()
  past_shows = []
  upcoming_shows = []

  for show in shows:
    show_data = {
      'artist_id': show.artist_id,
      'artist_name': show.Artist.name,
      'artist_image_link': show.Artist.image_link,
      'start_time': str(show.start_time)
    }
  if show.start_time < datetime.now():
    app.logger.warning('past show')
    past_shows.append(show_data)
  else:
    app.logger.warning('upcoming show')
    upcoming_shows.append(show_data)

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data) 
  
  
  

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)



@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)

  if form.validate():
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    website_link = form.website_link.data
    seeking_talent = True if form.seeking_talent.data == 'y' else False
    seeking_description = form.seeking_description.data
  else:
    flash(form.errors)
    return redirect(url_for('create_venue_submission'))

  search_name = db.session.query(Venue).filter(Venue.name.ilike(f"%{form.name.data}%")).all()
  if len(search_name) > 0:
    flash(f"Venue '{name}' already exists.")
    return redirect(url_for('create_venue_submission'))

  try:
    venue = Venue(
        name=name,
        city=city,
        state=state,
        address=address,
        phone=phone,
        facebook_link=facebook_link,
        image_link=image_link,
        website=website_link,
        seeking_talent=seeking_talent,
        seeking_description=seeking_description,
        genres=genres,
    )
    db.session.add(venue)
    db.session.commit()
    flash('Venue' + request.form['name'] + 'was successfully listed')
  except Exception as e:
    flash(f"Error {e} with inserting venue {form.name.data}.")
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    db.session.rollback()
    app.logger.warning(f'Error {e}')
  finally:
    db.session.close()
  return None






#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []

  artists = db.session.query(Artist)

  for artist in artists:
      x = {
          "id": artist.id,
          "name": artist.name
      }
      data.append(x)
  
  return render_template('pages/artists.html', artists=data)

  

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = db.session.query(Artist).filter(Artist.name.ilike(f"%{search_term}%")).all()
  data = []
  for artist in artists:
      shows = db.session.query(Show).filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()
      x = {
          "id": artist.id,
          "name": artist.name,
          "num_upcoming_shows": len(shows)
      }
      data.append(x)
  
  response = {
      "count": len(artists),
      "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

 

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()

  if artist is None:
    return render_template('errors/404.html')

  shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).all()
  past_shows = []
  upcoming_shows = []

  for show in shows:
    show_data = {
            "venue_id": show.venue_id,
            "venue_name": show.Venue.name,
            "venue_image_link": show.Venue.image_link,
            "start_time": str(show.start_time)
        }
    if show.start_time < datetime.now():
        app.logger.warning("past show!")
        past_shows.append(show_data)
    else:
        app.logger.warning("upcoming show!")
        upcoming_shows.append(show_data)

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

  

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  a = db.session.query(Artist).filter(Artist.id == artist_id).first()
  artist = {
      "id": a.id,
      "name": a.name,
      "genres": a.genres,
      "city": a.city,
      "state": a.state,
      "phone": a.phone,
      "website": a.website,
      "facebook_link": a.facebook_link,
      "seeking_venue": a.seeking_venue,
      "seeking_description": a.seeking_description,
      "image_link": a.image_link
  }

  return render_template('forms/edit_artist.html', form=form, artist=artist)
  
  

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()

  if not form.validate():
      flash(form.errors)
      return redirect(url_for('edit_artist_submission'))

  try:
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = True if form.seeking_venue.data == 'y' else False
      artist.seeking_description = form.seeking_description.data
      db.session.commit()
      flash(f"Artist {artist.name} successfully updated!")
  except Exception as e:
      flash(f"Error {e} with editing artist {form.name.data}.")
      db.session.rollback()
  finally:
      db.session.close()
  
  return redirect(url_for('show_artist', artist_id=artist_id))

  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()

  if not form.validate():
      flash(form.errors)
      return redirect(url_for('edit_venue_submission'))

  try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data
      venue.image_link = form.image_link.data
      venue.website_link = form.website_link.data
      venue.seeking_venue = True if form.seeking_venue.data == 'y' else False
      venue.seeking_description = form.seeking_description.data
      db.session.commit()
      flash(f"Venue {venue.name} successfully updated!")
  except Exception as e:
      flash(f"Error {e} with editing venue {form.name.data}.")
      db.session.rollback()
  finally:
      db.session.close()

  return render_template('forms/edit_venue.html', form=form, venue=venue)

  

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)

  if form.validate():
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    website_link = form.website_link.data
    seeking_venue = True if form.seeking_venue.data == 'y' else False
    seeking_description = form.seeking_description.data
  else:
    flash(form.errors)
    return redirect(url_for('create_artist_submission'))

  search_name = db.session.query(Artist).filter(Artist.name.ilike(f"%{form.name.data}%")).all()
  if len(search_name) > 0:
      flash(f"Artist '{name}' already exists.")
      return redirect(url_for('create_artist_submission'))   

  try:
      artist = Artist(
          name=name,
          city=city,
          state=state,
          phone=phone,
          facebook_link=facebook_link,
          image_link=image_link,
          website=website_link,
          seeking_venue=seeking_venue,
          seeking_description=seeking_description,
          genres=genres,
      )
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
      flash(f"Error {e} with inserting artist {form.name.data}.")
      db.session.rollback()
  finally:
      db.session.close()
  
  return render_template('pages/home.html')

  




#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows = db.session.query(Show)
  for show in shows:
    venue_name = db.session.query(Venue).filter(Venue.id == show.venue_id).first()
    artist_name = db.session.query(Artist).filter(Artist.id == show.artist_id).first()
    x = {
        "venue_id": show.venue_id,
        "venue_name": venue_name.name,
        "artist_id": show.artist_id,
        "artist_name": artist_name.name,
        "artist_image_link": artist_name.image_link,
        "start_time": str(show.start_time)
    }
    data.append(x)
  return render_template('pages/shows.html', shows=data)



@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)

  if form.validate():
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
  else:
    flash(form.errors)
    return redirect(url_for('create_show_submission'))  

  try:
      show = Show(
          artist_id=artist_id,
          venue_id=venue_id,
          start_time=start_time
      )
      db.session.add(show)
      db.session.commit()
      flash(f'Show was successfully listed!')
  except Exception as e:
      flash(f"Error {e} with inserting show.")
      db.session.rollback()
  finally:
      db.session.close()

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
