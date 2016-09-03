# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 13:52:52 2016

@author: eta2
"""

import sqlite3
import os

def getNewJobs(alreadythere=[]):
    ODBs=os.listdir('D:/users/eta2/hCxBvf/ODBs')
    ODBs=[ODB for ODB in ODBs if ODB not in alreadythere]
    folders=[ODB[:-4] for ODB in ODBs]
    return ODBs,folders
    
def getExistingJobNames(cursor):
    cursor.execute('SELECT jobName FROM jData')
    return cursor.fetchall()
    
def insertNewJobs(newODBs,newfolders,cursor):
    cursor.execute('SELECT max(jobID) FROM jData')
    result=cursor.fetchall()[0][0]
    if not result:
        result=0
    manynew=list(zip(list(range(result+1,result+len(newODBs))),
                     newODBs,
                     newfolders))
    cursor.executemany('INSERT INTO jData VALUES (?,?,?)',manynew)
    
def start():
    db=sqlite3.connect('db.db')
    c=db.cursor()
    return db,c

#%%
db,c=start()
alreadythere=[item[0] for item in getExistingJobNames(c)]
ODBs,folders=getNewJobs(alreadythere)
insertNewJobs(ODBs,folders,c)
db.commit()


    