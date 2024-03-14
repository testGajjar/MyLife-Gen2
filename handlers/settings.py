import datetime
from flask import Flask, request, render_template 
from google.appengine.ext import blobstore 

from models.settings import Settings
from models.userimage import UserImage
from models.timezones import timezones
from models.migratetask import MigrateTask
from templates import get_template  # Assuming you have a templates module
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class SettingsHandler(): 
    def get(self):
        settings = Settings.get()

        if not settings.blobstore_migration_done:
            migration_task_finished = bool(MigrateTask.query(MigrateTask.status == 'finished').get())
            if migration_task_finished:
                settings.blobstore_migration_done = True
                settings.put()
            else:
                if not UserImage.query().get():
                    settings.blobstore_migration_done = True
                    settings.put()

        return self._render(settings)

    def post(self):
        settings = Settings.get()

        settings.email_address = request.form.get('email-address')  # Update with form data
        settings.timezone = request.form.get('timezone')
        settings.email_hour = int(request.form.get('email-hour'))
        settings.dropbox_access_token = request.form.get('dropbox-access-token')
        settings.include_old_post_in_entry = request.form.get('include-old-entry') == 'yes'
        settings.put()
        return self._render(settings, saved=True)

    def _render(self, settings, saved=False):
        data = {
            "page" : "settings",
            "email_address" : settings.email_address,
            "dropbox_access_token" : settings.dropbox_access_token or "",
            "timezone" : settings.timezone,
            "timezones" : timezones,
            "email_hour" : settings.email_hour,
            "include_old_post_in_entry" : settings.include_old_post_in_entry,
            "upload_url" : blobstore.create_upload_url('/upload-finished'),  # From App Engine
            "saved" : saved,
            "can_migrate_images" : not settings.blobstore_migration_done,
            #"bucket_exists" : blobstore.bucket_exists(),  # From App Engine
            "version" : open('VERSION').read()
        }
        return render_template('settings.html', **data)
        #self.response.write(get_template('settings.html').render(data))

# Execution with Flask
if __name__ == '__main__':
    handler = SettingsHandler()  # Create a handler instance

    @app.route('/settings', methods=['GET', 'POST'])  # Add a route
    def settings_route():
        if request.method == 'GET':
            return handler.get()
        else:
            return handler.post()

    app.run(debug=True) 

