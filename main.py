from flask import Flask, render_template, redirect, request
from google.appengine.ext import ndb

from handlers.calendar import CalendarHandler
from handlers.dataupgrade import DataUpgradeHandler
from handlers.dropbox import DropboxBackupHandler
from handlers.edit import EditHandler, AddPhotoHandler, GetPhotoUploadUrlHandler, DeletePhotoHandler
from handlers.export import ExportHandler, ExportDeleteHandler, ExportDownloadHandler, ExportStartHandler, ExportStatusHandler
from handlers.frontpage import FrontPageHandler, FrontPagePostHandler
from handlers.image import ImageHandler
from handlers.migratecloudstorage import MigrateStartHandler, MigrateHandler, MigrateStatusHandler
from handlers.past import PastHandler
from handlers.postdates import PostDatesHandler
from handlers.receivemail import ReceiveMailHandler
from handlers.sendmail import SendMailHandler
from handlers.settings import SettingsHandler
from handlers.upload import UploadFinishedHandler, ImportHandler, ImportStatusHandler
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)


# These routes match the original webapp2 patterns precisely
@app.route('/')
def front_page():
    print('In Main.py: front_page()')
    return FrontPageHandler().get()


@app.route('/api/addphoto', methods=['POST'])
@app.route('/api/addphoto/<int:year>-<int:month>-<int:day>', methods=['POST'])
def add_photo(year=None, month=None, day=None):
    print('Inside add_photo')
    #print(request.form)
    #print('environ')
    #print(request.environ)
    #year = request.form['year']
    #month = request.form['month']
    #day = request.form['day']
    #environ = request.environ
    #print(request.form)
    
    return AddPhotoHandler().post(year, month, day)
    #year, month, day, environ)


@app.route('/api/photouploadurl')
@app.route('/api/photouploadurl/<int:year>-<int:month>-<int:day>')
def get_photo_upload_url(year=None, month=None, day=None):
    print('Inside get_photo_upload_url')
    print(request.form)
    return GetPhotoUploadUrlHandler().get(year, month, day)

@app.route('/api/<int:year>-<int:month>-<int:day>/<url_type>')
#@app.route('/api/<int:year>-<int:month>-<int:day>/prev')
#@app.route('/api/<int:year>-<int:month>-<int:day>/random')
def front_page_post(year, month, day, url_type):
    return FrontPagePostHandler().get(year, month, day, url_type)


@app.route('/write')
def calendar():
    return CalendarHandler().get()


@app.route('/dataupgrade')
def data_upgrade():
    return DataUpgradeHandler().get()


@app.route('/backup/dropbox')
def dropbox_backup():
    return DropboxBackupHandler().get()

@app.route('/edit/<int:year>-<int:month>-<int:day>', methods=['GET', 'POST', 'DELETE'])
@app.route('/write/<int:year>-<int:month>-<int:day>', methods=['GET', 'POST', 'DELETE'])
#@app.route('/(edit/write)/<selected_date>')
def edit(year, month, day):
    if request.method == 'GET':
        return EditHandler().get(request.path, year, month, day)
    elif request.method == 'POST':
        return EditHandler().post(year, month, day)
    elif request.method == 'DELETE':
        return EditHandler().delete_post(year, month, day)


@app.route('/export/delete')
def export_delete():
    return ExportDeleteHandler().get()


@app.route('/export/download/<path:filename>')
def export_download(filename):
    return ExportDownloadHandler().get(filename)


@app.route('/export/run')
def export():
    return ExportHandler().get()


@app.route('/export/start')
def export_start():
    return ExportStartHandler().get()


@app.route('/export/status/<task_id>')
def export_status(task_id):
    return ExportStatusHandler().get(task_id)


@app.route('/image/delete/<key>', methods=['POST'])
def delete_photo(key):
    return DeletePhotoHandler().post(key)


@app.route('/image/<key>')
def image(key):
    return ImageHandler().get(key)


@app.route('/import')
def import_():
    return ImportHandler().get()


@app.route('/import/status/<task_id>')
def import_status(task_id):
    return ImportStatusHandler().get(task_id)


@app.route('/migrate/start')
def migrate_start():
    return MigrateStartHandler().get()


@app.route('/migrate/run')
def migrate():
    return MigrateHandler().get()


@app.route('/migrate/status/<task_id>')
def migrate_status(task_id):
    return MigrateStatusHandler().get(task_id)

@app.route('/past', methods=['GET'])
@app.route('/past/<int:year>-<int:month>', methods=['GET'])
def past(year=None, month=None):
    return PastHandler().get(year, month)

@app.route('/postdates')
@app.route('/postdates/<int:year>-<int:month>', methods=['GET'])
def postDates(year=None, month=None):
    return PostDatesHandler().get(year, month)


@app.route('/sendmail')
def sendMail():
    return SendMailHandler().get()


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return SettingsHandler().get()
    elif request.method == 'POST':
        return SettingsHandler().post()


@app.route('/upload-finished', methods=['GET'])
def uploadFinished():
    return UploadFinishedHandler().get()


# ... Other routes as needed ...

if __name__ == '__main__':
    app.run(debug=True)

