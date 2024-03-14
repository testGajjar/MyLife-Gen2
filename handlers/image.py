from google.appengine.ext import blobstore
import filestore  # Assuming this has your Blobstore access functions
from models.userimage import UserImage
from flask import request

class ImageHandler(blobstore.BlobstoreDownloadHandler):
    def get(self, filename):

        image = UserImage.query(UserImage.filename == filename).get()

        #if request.get('fullsize'):
        key = image.original_size_key
        #else:
         #   key = image.serving_size_key

        if not image:
            self.error(404)
        else:
            headers = self.send_blob(request.environ, filestore.get_blob_key(key))
            headers["Content-Type"] = None
            return "", headers

class ImageUploadHandler(blobstore.BlobstoreUploadHandler):
    def post(self):
        # Assuming you save the blob_key to 'image.blob_key' in your model
        upload_files = self.get_uploads(request.environ, 'file')
        blob_info = upload_files[0]
        image = UserImage(blob_key=blob_info.key())
        # ... rest of your upload handling logic ... 

