#import webapp2
from templates import get_template
from flask import Flask, render_template 
from google.appengine.api import wrap_wsgi_app

# Initialize a Flask application
app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class CalendarHandler():
    def get(self):
        data = { "page" : "write"}

        # Use Flask's rendering capability
        return render_template('calendar.html', data=data)
        #self.response.write(rendered_template)

# (Optional) If you want to run this directly with Flask:
if __name__ == "__main__":
    app.run(debug=True) 



