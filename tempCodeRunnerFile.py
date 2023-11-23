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
    seeking_talent = db.Column(db.Boolean,nullable = False,default = False)
    seeking_description = db.Column(db.String(120))


    artist = db.relationship('Artist' , secondary = 'shows')
    show_relation = db.relationship('Show', backref='shows')
    


    # TODO: implement any missing fields, as a database migration using Flask-Migrate
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


    venue = db.relationship('Venue' , secondary = 'shows')
    show_relation = db.relationship('Show' , backref = 'shows')


    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
      return F"<Information Artist {self.id} {self.name} {self.genres}>"


class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer ,primary_key = True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"))
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"))
    start_time = db.Column(db.DateTime())

    venue_relation = db.relationship('Venue', backref='shows',overlaps = 'artist,show_relation,venue')
    artist_relation = db.relationship('Venue',backref ='artist',overlaps ='artist,show_relation')
