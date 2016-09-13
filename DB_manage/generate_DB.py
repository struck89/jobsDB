# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 15:14:31 2016

@author: eta2
"""

import os
import sqlite3 as sql
import numpy as np
import pandas as pd
import time

def create_DB(db_file,rootf='D:/users/eta2/hCxBvf',ODBsf='ODBs'):
    db=sql.connect(rootf+'/'+db_file)
    c=db.cursor()
    c.execute('drop table if exists jData;')
#    c.execute('drop table if exists jPV;')
    c.execute('create table jData(jID int, jName text);')
#    c.execute('''create table jPV(jID int, X real,
#              P1 real, P2 real, P3 real, P4 real, P5 real, P6 real, P7 real,
#              V1 real, V2 real, V3 real, V4 real, V5 real, V6 real, V7 real
#              );''')
    #now get all jobs in ./ODBs/ that have a folder in ./ with the same name
    ODBs_cand=os.listdir(rootf+'/'+ODBsf)
    ODBs_cand=[name[:-4] for name in ODBs_cand if name[-3:].lower()=='odb']
    ODBs=[folder for folder in os.listdir(rootf) if \
          (folder in ODBs_cand and \
           os.path.isdir(rootf+'/'+folder))]
    ODBs.sort()
    #insert all jobs and jobnames in DB
    what_to_insert=zip(range(1,len(ODBs)+1),ODBs)
    c.executemany('INSERT INTO jData VALUES (?,?)',list(what_to_insert))
    db.commit()
    return db,c
    
def insert_PV(c,resultsf='results',rootf='D:/users/eta2/hCxBvf'):
    c.execute('drop table if exists jPV;')
    c.execute('''create table jPV(jID int, X real,
              P1 real, P2 real, P3 real, P4 real, P5 real, P6 real, P7 real,
              V1 real, V2 real, V3 real, V4 real, V5 real, V6 real, V7 real
              );''')
    c.execute('SELECT jID, jName FROM jData;')
    jobs_in_jData=c.fetchall()
    jobs={name:ID for (ID,name) in jobs_in_jData}
    for name,ID in jobs.items():
        try:
            data=read_PV_result(rootf+'/'+resultsf+'/'+name+'_PV.csv')
            c.executemany(\
                'INSERT INTO jPV VALUES ({0}{1});'.format(ID,',?'*15),\
                data.as_matrix())
        except BaseException as err:
            print(str(err))
            print('Error when processing job {0} with ID {1}'.format(name,ID))
            print('We keep working anyway\n{0}'.format('_'*79))

def insert_facts(c,resultsf='results',rootf='D:/users/eta2/hCxBvf'):
    c.execute('drop table if exists jFacts;')
    c.execute('''create table jFacts(jID int, machine text,
              );''')
    c.execute('SELECT jID, jName FROM jData;')
    jobs_in_jData=c.fetchall()
    jobs={name:ID for (ID,name) in jobs_in_jData}
    for name,ID in jobs.items():
        try:
            data=read_facts(rootf,name)
            c.executemany(\
                'INSERT INTO jPV VALUES ({0}{1});'.format(ID,',?'*15),\
                data.as_matrix())
        except BaseException as err:
            print(str(err))
            print('Error when processing job {0} with ID {1}'.format(name,ID))
            print('We keep working anyways\n{0}'.format('_'*79))

def read_PV_result(file):
    result=pd.read_csv(file)
    clean=result.drop_duplicates('X')
    return clean

def read_facts(rootf,name):
    pass
    
#if __name__ == "__main__":
if True:
    start=time.clock()
    db,c=create_DB('dbtest4.db')
    insert_PV(c)
    db.commit()
    end=time.clock()
    print(end-start)
    