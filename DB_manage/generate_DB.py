# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 15:14:31 2016

@author: eta2
"""

import os
import sqlite3 as sql
import numpy as np
import pandas as pd

def create_DB(db_file,rootf='D:/users/eta2/hCxBvf',ODBsf='ODBs'):
    db=sql.connect(rootf+'/'+db_file)
    c=db.cursor()
    c.execute('drop table if exists jData;')
    c.execute('drop table if exists jPV;')
    c.execute('create table jData(jID int, jName text);')#, jFactsLocation text);')
    c.execute('''create table jPV(jID int, X real,
              P1 real, P2 real, P3 real, P4 real, P5 real, P6 real, P7 real,
              V1 real, V2 real, V3 real, V4 real, V5 real, V6 real, V7 real
              );''')
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
    c.execute('SELECT jID, jName FROM jData;')
    jNames=c.fetchall()
    jIDs=[element[0] for element in jNames]
    jNames=[element[1] for element in jNames]
    results_PV_files=os.listdir(rootf+'/'+resultsf)
    rPVf=results_PV_files
    #we build a list of results that are also in the jData list
    #we substract seven characters because it's the length of "_PV.csv"
    results_PV_files=[elem[:-7] for elem in rPVf if elem[:-7] in jNames]
    results_IDs=[jIDs[jNames.index(elem)] for elem in results_PV_files]
    for result,ID in zip(results_PV_files,results_IDs):
        data=read_PV_result(rootf+'/'+resultsf+'/'+result+'_PV.csv')
        c.executemany('''INSERT INTO jPV VALUES
        (%i,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''%ID,data.as_matrix())
    
    
def read_PV_result(file):
    result=pd.read_csv(file)
    clean=result.drop_duplicates('X')
    return clean
