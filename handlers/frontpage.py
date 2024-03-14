import datetime
import random
from flask import Flask, render_template, request
from google.appengine.ext import ndb  # Assuming you're using App Engine 

# Import your models (assuming they are adjusted to work with Flask/NDB)
from models.post import Post
from models.postcounter import PostCounter
from models.settings import Settings
from models.slug import Slug
from models.dailymail import DailyMail
from templates import get_template 
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class FrontPageHandler():
	def get(self):
		print('in FrontPageHandler.get()')
		settings = Settings.get() #Force email address update...
		print('settings')
		print(settings)
		posts = Post.query().order(-Post.date).fetch(1)
		print('After post')
		is_newest = True
		if posts:
			post = posts[0]
			is_oldest = post.date == Post.min_date()
		else:
			post = None
			is_oldest = True

        
		#See if this is the very first time we've been here. In that case
		#send an email immediately to get people started...
		first_time = False
		print('posts')
		print(post)
		print('before sending daily email')
 
		if not Slug.query().get() and not Post.query().get():
			first_time = True
			DailyMail().send(True)
		print('before rendering the template')

		return render_template('frontpage.html',
                           page="frontpage",
                           post=post,
                           is_oldest=is_oldest,
                           is_newest=is_newest,
                           first_time=first_time,
                           email=settings.email_address)

class FrontPagePostHandler():
	def get(self, year, month, day, type):
		date = datetime.date(int(year), int(month), int(day))
		min_date, max_date = Post.min_date(), Post.max_date()
		if type == 'prev':
			posts = Post.query(Post.date < date).order(-Post.date).fetch(1)
		elif type == 'next':
			posts = Post.query(Post.date > date).order(Post.date).fetch(1)
		elif type == 'random':
			count = PostCounter.get().count
			posts = Post.query().fetch(1, offset=random.randint(0, count-1))

		post = None
		if posts:
			post = posts[0]

		return render_template('frontpagepost.html',
                           page="frontpage",
                           post=post,
                           is_newest=post.date == max_date,
                           is_oldest=post.date == min_date)

# Adapt to Flask Style
#app.add_url_rule('/', view_func=FrontPageHandler.as_view('front_page'), methods=['GET'])
#app.add_url_rule('/<int:year>/<int:month>/<int:day>/<type>', view_func=FrontPagePostHandler.as_view('front_page_post'), methods=['GET']) 

if __name__ == '__main__':
    app.run()

