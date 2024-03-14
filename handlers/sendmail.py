from builtins import str
import datetime

from flask import Flask, request
from models.dailymail import DailyMail  # Assuming you have models.dailymail
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class SendMailHandler():  # Keep existing class structure
    def get(self):
        force = request.args.get('force', '0') == '1'
        date_str = request.args.get('date', None)

        if date_str:
            try:
                y, m, d = date_str.split('-')
                date = datetime.datetime(int(y), int(m), int(d)).date()
            except:
                return 'Invalid date, ignored', 400  # Error handling

        DailyMail().send(False, force, date)
        return 'Ran daily mail at ' + str(datetime.datetime.now())

# Adapt for Flask execution
if __name__ == '__main__':
    handler = SendMailHandler()  # Create an instance of the handler
    @app.route('/')  # Minimal route - adjust as needed
    def route_handler():
        return handler.get()

    app.run(debug=True)  # Start the Flask development server 

