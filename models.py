from connectors import db

class Albums(db.Model):
    id = db.Column('id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    cover = db.Column(db.String(100))  
    artist = db.Column(db.String(100))

    def __repr__(self):
        return '<Albums %r>' % self.name

class Songs(db.Model):
    id = db.Column('id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    album_id = db.Column(db.String(100))

    def __repr__(self):
        return '<Songs %r>' % self.name
