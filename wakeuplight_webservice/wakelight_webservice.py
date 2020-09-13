#!/usr/bin/python3
from flask import Flask, request
from flask_restful import reqparse, Resource, Api
from json import dumps
from crontab import CronTab
import requests

CRONTAB_FILE = "/etc/cron.d/wakelight"
DEVICE_ID = "<YOUR_DEVICE_ID>"
ACCESS_TOKEN = "<YOUR_PARTICLE_ACCESS_TOKEN>"
ON_COMMAND = 'curl https://api.particle.io/v1/devices/' + DEVICE_ID + '/wakeup -d access_token=' + ACCESS_TOKEN + ' -d "args=blah"'
OFF_COMMAND = 'curl https://api.particle.io/v1/devices/' + DEVICE_ID + '/rgbColor -d access_token=' + ACCESS_TOKEN + ' -d "args=0,0,0"'
WAKELIGHT_USER = 'root'

app = Flask(__name__)
api = Api(app)

try:
    cron = CronTab(tabfile=CRONTAB_FILE, user=False)
except FileNotFoundError:
    cron = CronTab()

def find_jobs(schedule_id):
    try:
        on_job = next(cron.find_comment(str(schedule_id) + ',on'))
    except StopIteration:
        on_job = cron.new(command=ON_COMMAND, user=WAKELIGHT_USER, comment=str(schedule_id) + ',on')
    print(on_job)
    try:
        off_job = next(cron.find_comment(str(schedule_id) + ',off'))
    except StopIteration:
        off_job = None
    print(off_job)

    return (on_job, off_job)

class Schedules(Resource):
    def get(self):
        data = {}
        for job in cron:
            schedule_id, schedule_state = job.comment.split(',')
            if not schedule_id in data:
                data[schedule_id] = {   'day'  :    str(job.dom),
                                        'month':    str(job.month),
                                        'dow'  :    str(job.dow),
                                        'enabled':  job.is_enabled(),
                                        }
            if schedule_state == "on":
                data[schedule_id]['ontime'] = { 'hour' :  str(job.hour),
                                                'minute': str(job.minute),
                                                }
            elif schedule_state == "off":
                data[schedule_id]['offtime'] =  { 'hour':     str(job.hour),
                                                  'minute':   str(job.minute)
                                                  }
        return data
    
    def post(self):
        args = reqparse.parse_args()

class AddSchedule(Resource):
    def __init__(self):
        self.editschedule = EditSchedule()

    def put(self):
        # Find last defined schedule id
        next_schedule_id = 1
        for job in cron:
            schedule_id, schedule_state = job.comment.split(',')
            schedule_id = int(schedule_id)
            if next_schedule_id <= schedule_id:
                next_schedule_id = schedule_id + 1
        
        self.editschedule.put(next_schedule_id)

class EditSchedule(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('onhour', type = str, required = True,
                help = 'No ON hour provided', location = 'json')
        self.reqparse.add_argument('onminute', type = str, required = True,
                help = 'No ON minute provided', location = 'json')
        self.reqparse.add_argument('offhour', type = str, location = 'json')
        self.reqparse.add_argument('offminute', type = str, location = 'json')
        self.reqparse.add_argument('day', type = str, required = True,
                help = 'No day provided', location = 'json')
        self.reqparse.add_argument('month', type = str, required =  True,
                help = 'No month provided', location = 'json')
        self.reqparse.add_argument('dow', type = str, required = True,
                help = 'No dow provided', location = 'json')
        self.reqparse.add_argument('enabled', type = bool, location = 'json')


    def put(self, schedule_id):
        args = self.reqparse.parse_args()
        print(args)

        on_job, off_job = find_jobs(schedule_id)

        on_job.setall(args['onminute'], args['onhour'], args['day'], args['month'], args['dow'])
        on_job.enable(args['enabled'])
        if args['offhour']:
            if not off_job:
                off_job = cron.new(command=OFF_COMMAND, user=WAKELIGHT_USER, comment=str(schedule_id) + ',off')
            off_job.setall(args['offminute'], args['offhour'], args['day'], args['month'], args['dow'])
            off_job.enable(args['enabled'])
        else:
            if off_job:
                cron.remove(off_job)

        if not cron.filen:
            cron.write(filename=CRONTAB_FILE)
        else:
            cron.write()

    def delete(self, schedule_id):
        on_job, off_job = find_jobs(schedule_id)

        cron.remove(on_job)
        if off_job:
            cron.remove(off_job)
        removed_schedule_id = schedule_id

        # shift all next ids
        for job in cron:
            schedule_id, schedule_state = job.comment.split(',')
            schedule_id = int(schedule_id)
            if removed_schedule_id < schedule_id:
                job.set_comment(str(schedule_id - 1) + ',' + schedule_state)

        cron.write()
        
class EditScheduleState(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('enabled', type = bool, required = True,
                help = 'No enabled state provided', location = 'json')

    def put(self, schedule_id):
        args = self.reqparse.parse_args()

        on_job, off_job = find_jobs(schedule_id)

        on_job.enable(args['enabled'])
        print('%s - %s' % (args['enabled'], on_job))
        if off_job:
            off_job.enable(args['enabled'])
            print('%s - %s' % (args['enabled'], off_job))

        cron.write()

class SetRGB(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('rgb', type = str, required = True,
                help = 'No rgb color provided', location = 'json')

    def put(self):
        args = self.reqparse.parse_args()

        data = {
                'access_token': ACCESS_TOKEN,
                'args': args['rgb']
                }

        r = requests.post('https://api.particle.io/v1/devices/' + DEVICE_ID + '/rgbColor', data=data)
        print(str(r.status_code) + " - " + r.text)

api.add_resource(Schedules, '/schedules')
api.add_resource(AddSchedule, '/addschedule')
api.add_resource(EditSchedule, '/editschedule/<int:schedule_id>')
api.add_resource(EditScheduleState, '/editschedulestate/<int:schedule_id>')
api.add_resource(SetRGB, '/setRGB')

if __name__ == '__main__':
     app.run(host='0.0.0.0', port='5002')
