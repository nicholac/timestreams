
import os
import sys
import logging
#from pymongo import MongoClient
import json
import random
from bson.code import Code
from code import *

from flask import Flask, render_template, jsonify, g, request, Response
from flask.ext.pymongo import PyMongo

# Ensure paths then use . package notation and __init__ files.
this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if this_dir not in sys.path:
    sys.path.append(this_dir)

# Basic lagging configuration
logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO, filename=r'/home/ubuntu/timestreams.log')
logger = logging.getLogger(__name__)


# Flask App configuration
app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = ''
app.name = 'streamgraph'
print app.name
#mongo = PyMongo(app)
#app.run(host= '127.0.0.1')

# ----------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------

@app.route('/')
def indexPath():
    """ normal http request to a serve up the page """


    return render_template('index.html')

@app.route('/data')
def data():
    bounds = request.args.get('bounds', None).split(',')
    for idx, b in enumerate(bounds):
        bounds[idx]=float(b)
    #Bounds as: llx, lly, urx, ury
    #Some test data - works
    out = [{"key":"AR", "value":0.1, "date":"01/08/13"},
           {"key":"AR", "value":0.15, "date":"01/09/13"},
           {"key":"AR", "value":0.38, "date":"01/10/13"},
           {"key":"AR", "value":0.22, "date":"01/11/13"},
           {"key":"AR", "value":0.9, "date":"01/12/13"},
           {"key":"AL", "value":0.11, "date":"01/08/13"},
           {"key":"AL", "value":0.0, "date":"01/09/13"},
           {"key":"AL", "value":0.3, "date":"01/10/13"},
           {"key":"AL", "value":0.0, "date":"01/11/13"},
           {"key":"AL", "value":0.7, "date":"01/12/13"}]

    print bounds


    out2 = [{"date": "2011-06-06T00:00:00+01:00", "value": 7.0, "key": "testdotstz"},
            {"date": "2011-06-13T00:00:00+01:00", "value": 25.0, "key": "testdotstz"}]

    #Load supported databases
    dbs = loadDBsFile()
    #Get all the supported tables
    supTabs = getSupdTables(dbs)
    #Convert the data for internal pg2D3 func - first run
    dsData = dsDataconv(supTabs)
    #Make d3Data
    d3Data = pg2D3(dsData, 'month', bounds)
    #print d3Data[0:10]

    return Response(json.dumps(d3Data),  mimetype='application/json')

'''
@app.route('/persondata')
def personData():
    #Takes in the selected name, gets data from db and returns data ready for graphing
    name = request.args.get('person', None)
    rec = mongo.db.people.find({'name':name})
    out = rec.next()
    #Remove the object id
    del out['_id']
    #print out
    return jsonify(out)
'''

if __name__ == '__main__':

    app.run(host='0.0.0.0', port='80')







