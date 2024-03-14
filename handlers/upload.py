from flask import Flask, request, jsonify, redirect, render_template
from future import standard_library
import zipfile
import datetime
import re
import io
import logging
import json
import traceback
from google.appengine.ext import ndb
from google.appengine.ext.blobstore import BlobstoreUploadHandler, BlobstoreDownloadHandler
from google.appengine.api import taskqueue
from errorhandling import log_error
from google.appengine.api import wrap_wsgi_app

# Replace with your models based on your new database choice
# ... e.g., using SQLAlchemy:
# from mymodels import Post, ImportTask, UserImage, PostCounter

standard_library.install_aliases()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)


class UploadFinishedHandler(BlobstoreUploadHandler):
    def post(self):
        file_info = request.files['file']  # Adapt how file is accessed

        task = ImportTask(uploaded_file=file_info.filename)  # Adjust accordingly
        task.put()

        # Adapt task queuing mechanism for Flask environment
        queue_import_task(task.key.urlsafe())

        result = {"message": "Upload finished, starting import...", "id": task.key.urlsafe()}
        self.response.headers['Content-Type'] = "application/json"
        self.response.write(json.dumps(result))


class ImportHandler(object):
    def post(self):
        import_task_key = request.form.get('task')  # Adjust key retrieval
        import_task = import_task_key.get()
        import_task.update('Unpacking zip file...', status='inprogress')

        logging.info('Starting import ...')
        counter = PostCounter.get()

        try:
            posts, images = self.read_zip_file(request.environ, import_task.uploaded_file)
            import_task.update('Importing...', total_photos=len(images), total_posts=len(posts))
            logging.info('Importing %s posts, %s images' % (len(posts), len(images)))

            posts = self.filter_posts(posts)  # May need changes based on your model

            for date, text in posts:
                str_date = date.strftime('%Y-%m-%d')

                p = Post(date=date, source='ohlife', text=text.decode('utf-8'))
                p.images = []
                p.has_images = False

                post_images = [(k, images[k]) for k in list(images.keys()) if str_date in k]

                if len(post_images):
                    logging.info('Importing %s images for date %s' % (len(post_images), str_date))
                    p.images = []
                    p.has_images = True
                    for name, bytes in post_images:
                        user_image = UserImage()
                        img_name = name.replace('img_', '').replace('.jpeg', '.jpg')
                        user_image.import_image(request.environ, img_name, name, bytes, date)
                        p.images.append(img_name)
                        import_task.imported_photos += 1
                        user_image.put()

                p.put()
                counter.increment(p.date.year, p.date.month, False)

                import_task.imported_posts += 1
                if import_task.imported_posts % 10 == 0:
                    import_task.update('Imported %s/%s post, %s/%s photos...' % (
                        import_task.imported_posts, import_task.total_posts, import_task.imported_photos,
                        import_task.total_photos))
                    logging.info(import_task.message)
                    counter.put()

            counter.put()

            skipped_posts = import_task.total_posts - import_task.imported_posts
            skipped_photos = import_task.total_photos - import_task.imported_photos
            msg = 'Imported %s posts and %s photos.' % (import_task.imported_posts, import_task.imported_photos)
            if skipped_posts or skipped_photos:
                msg += ' %s posts and %s photos already existed and were skipped.' % (skipped_posts, skipped_photos)

            import_task.update(msg, status='finished')
            logging.info(import_task.message)

            # Adapt this based on your storage 
            # filestore.delete(import_task.uploaded_file)

        except Exception as ex:
            # TODO: Adapt error handling and logging
            import_task.update('Failed to import: %s' % ex, status='failed')
            log_error('Failed import', traceback.format_exc(6))  

    def read_zip_file(self, request_environ, uploaded_file):
        # ... (Adapt data loading; replace filestore with your storage solution)
        blob_info = blobstore.BlobInfo.get(uploaded_file)
        blob_reader = blobstore.BlobReader(blob_info)

        zip = zipfile.ZipFile(io.BytesIO(blob_reader.read()))

        # ... (The rest of the code remains the same)

    def filter_posts(self, new_posts):
        # ... (May need changes based on your model)
        print('filtering posts')


class ImportStatusHandler(object):
    def get(self, id):
        import_task = ndb.Key(urlsafe=id).get()

        result = {"status": import_task.status, "message": import_task.message}
        self.response.headers['Content-Type'] = "application/json"
        self.response.write(json.dumps(result))

if __name__ == '__main__':
    app.run(debug=True)


