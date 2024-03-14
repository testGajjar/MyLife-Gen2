import datetime
import json
from flask import Flask, jsonify

# Import your existing models 
from models.post import Post

# (Assuming you continue to use google.appengine.ext.ndb for data access)
from google.appengine.ext import ndb
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class PostDatesHandler:  # Maintain your class structure
    def get(self, year, month):
        year, month = int(year), int(month)
        from_date = datetime.date(int(year), int(month), 1)
        next_month = from_date + datetime.timedelta(days=33)
        to_date = datetime.date(next_month.year, next_month.month, 1)

        days = [p.date.day for p in Post.query(
            ndb.AND(Post.date >= from_date, Post.date < to_date)).order(-Post.date).fetch()
        ]

        return jsonify({"key": from_date.strftime('%Y-%m'), "days": days})

@app.route('/postdates/<int:year>/<int:month>')
def get_post_dates_flask(year, month):
    handler = PostDatesHandler()
    return handler.get(year, month)

if __name__ == '__main__':
    app.run(debug=True) 

