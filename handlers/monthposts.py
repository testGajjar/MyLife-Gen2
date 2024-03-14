import datetime
import json
import random

from flask import Flask, jsonify  # Import Flask components
from templates import get_template 
from models.post import Post
from models.postcounter import PostCounter
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)  # Create Flask app
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class MonthPostsHandler(): 
    def get(self, year, month):
        from_ = datetime.date(int(year), int(month), 1)

        posts = Post.query(Post.date < from_).order(-Post.date).fetch(1)

        result = {
            "year": year,
            "month": month,
            "days": [p.date.day for p in posts]
        }

        return jsonify(result) 

# Map route with Flask directly
@app.route('/<int:year>/<int:month>', methods=['GET']) 
def month_posts(year, month):
    handler = MonthPostsHandler()
    handler.initialize(app.request, app.response)  # Simulate webapp2 initialization
    handler.get(year, month)
    return handler.response 

if __name__ == '__main__':
    app.run(debug=True)  # Start Flask app (in debug mode for development)

