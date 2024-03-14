from __future__ import with_statement  
import logging
import json
import traceback

from flask import Flask, request, jsonify
from google.appengine.ext import ndb
from google.appengine.api import taskqueue  

from models.migratetask import MigrateTask   
from models.userimage import UserImage 
from errorhandling import log_error
from google.appengine.api import wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

class MigrateStartHandler: # Maintain class structure
    def post(self):
        task = MigrateTask()
        task.put()

        retry_options = taskqueue.TaskRetryOptions(task_retry_limit=0)
        queue_task = taskqueue.Task(url='/migrate/run', params={"task": task.key.urlsafe()}, retry_options=retry_options)
        queue_task.add()

        return jsonify({
            "message": "Migration queued and will start in a few seconds...",
            "id": task.key.urlsafe()
        })

class MigrateHandler: # Maintain class structure
    def post(self):
        task_key = ndb.Key(urlsafe=request.args.get('task')) # Use request.args in Flask
        task = task_key.get()

        task.update('Starting migration...', status='inprogress')
        logging.info('Starting migration ...')

        try:
            images = [i for i in UserImage.query() if i.filename != i.original_size_key]

            task.update('Migrating...', total_images=len(images))
            logging.info('Migrating %s images' % len(images))

            for img in images:
                img.migrate_to_gcs()
                task.migrated_images += 1
                if task.migrated_images % 3 == 0:
                    task.update('Migrated %s/%s images' % (task.migrated_images, task.total_images))
                    logging.info(task.message)
                    task.put()

            task.update('Finished migrating images. Have a nice day :)', status='finished')
            logging.info(task.message)

        except Exception as ex:
            task.update('Failed to migrate: %s' % ex, status='failed')
            log_error('Failed migrate images', traceback.format_exc(6))

class MigrateStatusHandler:
    def get(self, id):
        task = ndb.Key(urlsafe=id).get()
        return jsonify({
            "status": task.status,
            "message": task.message
        })

# Map routes to handler classes 
#app.add_url_rule('/migrate/start', view_func=MigrateStartHandler.as_view('migrate_start', methods=['POST']))
#app.add_url_rule('/migrate/run', view_func=MigrateHandler.as_view('migrate_run', methods=['POST']))
#app.add_url_rule('/migrate/status/<id>', view_func=MigrateStatusHandler.as_view('migrate_status'))

if __name__ == '__main__':
    app.run()  

