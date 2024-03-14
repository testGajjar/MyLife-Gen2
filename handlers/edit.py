import datetime
import logging
import json
import filestore
from flask import Flask, request, jsonify, render_template, redirect
from google.appengine.ext import ndb
from google.appengine.ext.blobstore import BlobstoreUploadHandler, BlobstoreDownloadHandler
from google.appengine.api import app_identity

# Import your models (assuming they are adjusted to work with Flask/NDB)
from models.post import Post
from models.postcounter import PostCounter
from models.userimage import UserImage
from models.rawmail import RawMail

# Assuming you have templates like 'edit.html' 
from templates import get_template
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class GetPhotoUploadUrlHandler():
  def get(self, year, month, day):
    upload_url = filestore.create_upload_url('/api/addphoto/' + str(year) + '-' + str(month) + '-'+ str(day))
    print('Uploading URL, GetPhotoUploadUrlHandler.get()')
    print(request.form)
    print('upload_url')
    print(upload_url)
    return jsonify({"upload_url": upload_url})

class AddPhotoHandler(BlobstoreUploadHandler):
  def post(self, year, month, day):
  #, year, month, day, environ):
    # Incorporate request.environ
    print('Inside AddPhotoHandler.post()')
    file_infos = self.get_file_infos(request.environ)
    
    print('file_infos')
    print(file_infos)
    file_info = file_infos[0]
    print('before date')
    print(request.form)
    print('before date')
    print(request.args)
    print('before date')
    print(request.data)
    print('before date')
    print(request)

    #year = int(request.form['year'])
    print('year')
    print(year)
    #month = int(request.form.get('month'))
    #day = request.form.get('day')
    date = datetime.datetime(int(year), int(month), int(day))
    print('date')
    print(date)

    if file_info.content_type.lower() not in (
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp'):
      return jsonify({
        "status": "error",
        "message": "Unsupported content type: " + file_info.content_type
       })

    bytes = filestore.read(file_info.gs_object_name)
    print('read file')
    existing_images = [u.filename for u in UserImage.query(UserImage.date == date).fetch()]

    filename = UserImage.create_image_name(file_info.filename, date, existing_images)
    img = UserImage()
    img.import_image(filename, file_info.filename, bytes, date, None)
    img.put()
    filestore.delete(file_info.gs_object_name)

    post = Post.query(Post.date == date).get()
    if post:
      post.has_images = True
      if post.images is None:
        post.images = []
      post.images.append(filename)
      post.put()

    return jsonify({"status": "ok", "filename": filename})

class DeletePhotoHandler(BlobstoreUploadHandler):
  def post(self, filename):
    #self.response.headers['Content-Type'] = "application/json"
    img = UserImage.query(UserImage.filename == filename).get()
    if not img:
      return jsonify({"status": "error", "message": "Image does not exist"})

    post = Post.query(Post.date == img.date).get()
    if post:
      try:
        post.images.remove(filename)
        post.text = post.text.replace('$IMG:' + filename, '').replace('\n\n\n\n', '\n\n')
      except:
        pass

      if len(post.images) == 0:
        post.has_images = False

      post.put()

    filestore.delete(img.serving_size_key)
    filestore.delete(img.original_size_key)
    img.key.delete()

    return jsonify({"status": "ok"})


class EditHandler(BlobstoreUploadHandler):
  def get(self, path, year, month, day):
    print('Inside EditHandler.get()')
    print(path)
    kind = path.split("/")[1]
    print(kind)
    date = datetime.datetime(int(year),int(month),int(day)).date()
    post = Post.query(Post.date == date).get()
    if kind == 'write' and post:
      return self.redirect('/edit/%s' % date.strftime('%Y-%m-%d'))
    if kind == 'edit' and not post:
      return self.redirect('/write/%s' % date.strftime('%Y-%m-%d'))

    data = { "date" : date, "text" : "", "page" : "write", "kind" : kind}
    if post:
      data["page"] = "edit"
      data["text"] = post.text
      data["images"] = post.images
    else:
      data["images"] = [u.filename for u in UserImage.query(UserImage.date == date).fetch()]

    return render_template('edit.html', **data)

   

  def post(self, year, month, day):
    print('Inside EditHandler.post()')
    date = datetime.datetime(int(year),int(month),int(day)).date()
    post = Post.query(Post.date == date).get()
 
    is_new = False
    if not post:
      post = Post(date=date, source='web',images=[])
      is_new = True
 
    post.text = request.form['text']

    save = request.form['action'] == 'save'
    delete = request.form['action'] == 'delete'

    if save and delete:
      raise Exception('Something weird happened...')

    if save:
      if is_new:
        post.images = [u.filename for u in UserImage.query(UserImage.date == date).fetch()]
        post.images.sort()
        post.has_images = True

      post.put()
      if is_new:
        PostCounter.get().increment(post.date.year, post.date.month)

      return self.redirect_to_date(post.date)
    elif delete:
      self.delete_post(post)

      next_post = Post.query(Post.date > date).order(Post.date).get()
      if next_post and next_post.date.month == date.month:
        return self.redirect_to_date(next_post.date)

      #No way, we'll have to just redirect to the empty month
      return redirect('/past/%s' % date.strftime('%Y-%m'))
    else:
      raise Exception('How the hell did we get here...?')

  def delete_post(self, post):
    print('Inside EditHandler.delete()')
    images = UserImage.query(UserImage.date == post.date).fetch()

    for img in images:
      filestore.delete(img.serving_size_key)
      filestore.delete(img.original_size_key)
      img.key.delete()

    emails = RawMail.query(RawMail.date == post.date).fetch()
    for email in emails:
      email.key.delete()

    post.key.delete()
    PostCounter.get().decrement(post.date.year, post.date.month)
 
    logging.info('Deleted %s images, %s emails and 1 post from %s' % (len(images), len(emails), post.date.strftime('%Y-%m-%d')))
 
  def redirect_to_date(self, date):
    print('Inside EditHandler.redirect_to_date()')
    return redirect('/past/%s#day-%s' % (date.strftime('%Y-%m'), date.day))

if __name__ == '__main__':
    app.run()

