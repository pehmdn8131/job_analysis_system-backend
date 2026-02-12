from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salary_min = db.Column(db.Integer)
    city = db.Column(db.String(50))
