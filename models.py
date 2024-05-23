from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
    shows_venues = db.relationship('Show', backref=db.backref('venues'),lazy=True)
    


    def __repr__(self):
        return f"<Information Venue {self.id} {self.name}>"


    def to_dict(self):
        return{
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'address': self.address,
            'phone': self.phone,
            'genres': self.genres,
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'seeking_talent': self.seeking_talent,
            'seeking_description': self.seeking_description
        }  


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
    seeking_venue = db.Column(db.Boolean,default=False)
    seeking_description = db.Column(db.String(120))


    venues = db.relationship('Venue' , secondary = 'shows')
    shows_artists = db.relationship('Show' , backref =db.backref('artists'),lazy =False)


    def __repr__(self):
        return F"<Information Artist {self.id} {self.name} {self.genres}>"


    def to_dict(self):
        return{
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'genres': self.genres,
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'seeking_venue': self.seeking_venue,
            'seeking_description': self.seeking_description 
        }

class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer ,primary_key = True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"))
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"))
    venue_name = db.Column(db.String(120))
    artist_name = db.Column(db.String(120))
    artist_image_link = db.Column(db.String(500))
    start_time = db.Column(db.DateTime())

    venue_relation = db.relationship('Venue',back_populates='shows_venues')
    artist_relation = db.relationship('Artist',back_populates='shows_artists')
