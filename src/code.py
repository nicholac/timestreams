'''
Created on 12 Dec 2014

@author: dusted
'''
from random import randint, random
from datetime import datetime, timedelta
import psycopg2
import json
import os


def pg2D3(dsData, binVal, bounds):
    '''Takes in a bounding geometry box, and selected datasets, gets data over this area and
    returns array for outjsonify to d3
    ds: [{'tabs': [{'geomCol': 'the_geom', 'tabName': 'testdotstz', 'tsCol': 'time_stamp'}], 'dbIndex': 0, 'dbName': u'dusted'}]
    bin = string representing the pgsql date trunc binning
    out = [{"key":"AR", "value":0.1, "date":"01/08/13"},
           {"key":"AR", "value":0.15, "date":"01/09/13"}]
    '''
    #Get the connection params
    dbs = loadDBsFile()
    out = []
    dtgList = []
    maxVal = 0.0
    for ds in dsData:
        pgConn = psycopg2.connect(database=dbs[ds['dbIndex']]['db'],
                                  user=dbs[ds['dbIndex']]['user'],
                                  host=dbs[ds['dbIndex']]['host'],
                                  password=dbs[ds['dbIndex']]['password'])
        cur = pgConn.cursor()
        #Get the data from pg
        for tab in ds['tabs']:
            thisTab = []
            #Get the geom bounds from bounds
            sql = 'select st_geomfromtext(\'POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))\',4326)'
            data = [bounds[0], bounds[1], bounds[0], bounds[3], bounds[2], bounds[3], bounds[2],bounds[1], bounds[0], bounds[1]]
            cur.execute(sql, data)
            res = cur.fetchall()
            polyGeom = res[0][0]
            #Note - counting the geom field in case oid doesnt exist
            #Original without geometry select - works
            #sql = 'select count('+ tab['geomCol'] +'), date_trunc(\''+binVal+'\','+ tab['tsCol'] +') as '+ tab['tsCol'] +' FROM '+ tab['tabName'] +' GROUP BY date_trunc(\''+binVal+'\','+ tab['tsCol'] +') ORDER BY '+ tab['tsCol']
            sql = 'select count('+ tab['geomCol'] +'), date_trunc(\''+binVal+'\','+ tab['tsCol'] +') as '+ tab['tsCol'] +' FROM '+ tab['tabName'] +' WHERE st_intersects(%s,the_geom) GROUP BY date_trunc(\''+binVal+'\','+ tab['tsCol'] +') ORDER BY '+ tab['tsCol']
            data = [polyGeom]
            cur.execute(sql, data)
            res = cur.fetchall()
            for rec in res:
                #convert to jsonisable
                #dtg = rec[1].isoformat()
                if float(rec[0]) > maxVal:
                    maxVal = float(rec[0])
                dtg = rec[1].strftime("%m/%d/%y")
                thisTab.append({"key":tab['tabName'], "value":float(rec[0]), "date":dtg})
                #Record in the master dtg list for later combination
                if rec[1] not in dtgList:
                    dtgList.append(rec[1])
            if len(thisTab)>0:
                out.append(thisTab)
        pgConn.close()

    #Now normalise all the values 0-1
    for tab in out:
        for i in tab:
            i['value']= i['value']/maxVal

    #Sort out the date lists - padding out with zeros
#TODO: There is a much better way to do this - either earlier in this code or without the nesting in JS
    dtgList = sorted(dtgList)
    newOut = []
    inCheck = False
    for dtg in dtgList:
        for tab in out:
            for d in tab:
                if d['date'] == dtg.strftime("%m/%d/%y"):
                    #Match - add it in
                    inCheck = True
                    newOut.append(d)
                else:
                    continue
            #Check if we found it and do relevant thing
            if not inCheck:
                #Didnt find anything - add in a blank for this date
                oDtg = dtg.strftime("%m/%d/%y")
                newOut.append({"key":tab[0]['key'], "value":0.0, "date":oDtg})
            else:
                inCheck = False

    del out
    del dtgList
    return newOut

def dsDataconv(inData):
    '''For use when no data sets are selected from the map - like on first load
    Just converts between the supported datasets type to that expected by the pg2D3 algorithm
    '''
    #Mini function for converting suptablse into the input for pg2D3 func
    #In practice this should be done on page load / selection of datasets
    dsData = []
    for tab in inData:
        d = {'tabs': [], 'dbIndex': tab['dbIndex'], 'dbName': tab['dbName']}
        for t in tab['supTabs']:
            d['tabs'].append({'geomCol':t['geomCols'][0], 'tsCol':t['tsCols'][0], 'tabName':t['tabName']})

        dsData.append(d)
    return dsData

def getSupdTables(inDbs):
    '''Searches a given databse for supported tables
    i.e. - geom and time
    '''
    #connect to supported db's
    out = []
    for idx, db in enumerate(inDbs):
        try:
            pgConn = psycopg2.connect(database=db['db'],user=db['user'],host=db['host'],password=db['password'])
        except:
            print 'Failed to connect to a db: '+db['db']
            continue
        #get a list of tables
        cur = pgConn.cursor()
        #At the moment only public schema is supported...
        sql = 'SELECT table_name FROM information_schema.tables WHERE table_schema=\'public\' AND table_type=\'BASE TABLE\''
        cur.execute(sql)
        res = cur.fetchall()
        #Check all the returned tables for timestamps and geoms
        supTabs = []
        for tab in res:
            tsFields = []
            geomFields = []
            tabName = tab[0]
            sql = 'SELECT column_name, data_type FROM information_schema."columns" WHERE "table_name"=%s'
            cur.execute(sql, [tab[0]])
            #Res now has coumn names and data types
            res = cur.fetchall()
            #Check if there is a timestamp and a geom
#TODO: Support timestamps without TZ
            for col in res:
                if col[1] == 'timestamp with time zone':
                    tsFields.append(col[0])
                elif col[1] == 'USER-DEFINED':
                    #Check for valid geometries
                    sql = 'SELECT ST_IsValid('+ col[0] +') from '+tab[0]+' limit 1'
                    cur.execute(sql)
                    res = cur.fetchall()
                    if res[0][0] == True:
                        geomFields.append(col[0])
                else:
                    continue
            #If its a supported table them record and continue
            if len(tsFields)>0 and len(geomFields)>0:
                supTabs.append({'tabName':tabName, 'geomCols':geomFields, 'tsCols':tsFields})
#TODO: remember we might have multiple geom or ts cols - recording all now, build supoprt for multiple later
        #Done a database - remember all the supported tables
        #Idx here so we dont have to throw around db conn params
        if len(supTabs)>0:
            out.append({'dbIndex':idx, 'dbName':db['db'], 'supTabs':supTabs})
        pgConn.close()

    return out


def loadDBsFile():
    '''Loads in the list of supported databases from json file
    this is a static file containing logins etc for the db
    Returns dictionaries of conn params
    [{'supTabs': [{'geomCols': ['the_geom'], 'tabName': 'testdotstz', 'tsCols': ['time_stamp']}], 'dbIndex': 0, 'dbName': u'dusted'}]
    '''
    #Get file locat
    thisDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #Open json
    fp = open(thisDir+r'/src/static/data/dbs.json', 'rb')
    out = json.load(fp)
    fp.close()
    return out


def genRandPt():
    '''Just generates a random point
    '''
    lng = randint(-179,179)+random()
    lat = randint(-89,89)+random()
    #lng = randint(-179,179)+random()
    #lat = randint(-89,89)+random()
    dtg = datetime.now()+timedelta(days=randint(-500, -220))
    return [lng,lat,dtg]


def ingestRandPts(numPts, tableName, category):
    '''Inserts a given number of points of given category into a table
    '''
    pgConn = psycopg2.connect(database='dusted', user='dusted', host='localhost')
    cur = pgConn.cursor()
    for i in range(0,numPts):
        print i
        randPt = genRandPt()
        #print randPt
        sql = 'select st_geomfromtext(\'POINT(%s %s)\',4326)'
        cur.execute(sql, [float(randPt[0]), float(randPt[1])])
        res = cur.fetchall()
        geom = res[0][0]
        sql = 'insert into '+ tableName +'(time_stamp, the_geom, category) values(%s, %s, %s)'
        cur.execute(sql, [randPt[2], geom, category])
    pgConn.commit()
    del cur
    pgConn.close()
    return


if __name__ == '__main__':
    ingestRandPts(500, 'testdots2tz', 'catA')
    '''
    dbs = loadDBsFile()
    #Get all the supported tables
    supTabs = getSupdTables(dbs)
    #Convert the data for internal pg2D3 func
    dsData = dsDataconv(supTabs)
    #Make d3Data
    pg2D3(dsData, 'month')
    '''





