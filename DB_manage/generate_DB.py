# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 15:14:31 2016

@author: eta2
"""

import os
import sqlite3 as sql
import pandas as pd
import time
from datetime import datetime
from hashlib import md5

def hashstr(name):
    return md5(name.lower().encode()).hexdigest()[-6:].upper()

def create_DB(db_file,rootf='D:/users/eta2/hCxBvf',ODBsf='ODBs'):
    db=sql.connect(rootf+'/'+db_file)
    c=db.cursor()
    c.execute('drop table if exists jData;')
    c.execute('create table jData(jID int, jName text, jHash text);')
    #now get all jobs in ./ODBs/ that have a folder in ./ with the same name
    ODBs_cand=os.listdir(rootf+'/'+ODBsf)
    ODBs_cand=[name[:-4] for name in ODBs_cand if name[-3:].lower()=='odb']
    ODBs=[folder for folder in os.listdir(rootf) if \
          (folder in ODBs_cand and \
           os.path.isdir(rootf+'/'+folder))]
    ODBs.sort()
    hashes=[hashstr(name) for name in ODBs]
    #insert all jobs and jobnames in DB
    what_to_insert=zip(range(1,len(ODBs)+1),ODBs,hashes)
    c.executemany('INSERT INTO jData(jID,jName,jHash) VALUES (?,?,?)',\
                  list(what_to_insert))
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
            columns=['jID']+list(data.columns)
            c.executemany(\
              'INSERT INTO jPV('+','.join(columns)+') VALUES ({0}{1});'\
                .format(ID,',?'*15),data.as_matrix())
        except Exception as err:
            print(str(err))
            print('Error when processing job {0} with ID {1}'.format(name,ID))
            print('We keep working anyway\n{0}'.format('_'*79))

def insert_facts(c,rootf='D:/users/eta2/hCxBvf'):
    c.execute('drop table if exists jFacts;')
    c.execute('''create table jFacts(jID int, duration real, duration2 text,
                 start text, end text, machine text, cores int, steps int,
                 prel_duration real, sec_computed real
              );''')
    c.execute('SELECT jID, jName FROM jData;')
    jobs_in_jData=c.fetchall()
    jobs={name:ID for (ID,name) in jobs_in_jData}
    for name,ID in jobs.items():
        try:
            dictio=read_facts(name,rootf=rootf)
            columns=['jID']+list(dictio.keys())
            c.execute(\
                'INSERT INTO jFacts({2}) VALUES ({0}{1});'\
                .format(ID,',?'*len(dictio),','.join(columns)),\
                tuple(dictio.values()))
        except Exception as err:
            print(str(err))
            print('Error when processing job {0} with ID {1}'.format(name,ID))
            print('We keep working anyways\n{0}'.format('_'*79))

def insert_materials(c,rootf='D:/users/eta2/hCxBvf'):
    materials=['a','b','af','bf','a_s','bs','afs','bfs','D',\
               't0','m','b_tr','l0','B_ECa','Ca0max','Ca0','Tmax',\
               'Frac_Lat','ip','lr']
    sql_create_table=' real, '.join(materials)+' real'
    sql_fill_table=','.join(materials)
    parts=['RA','RV','LA','LV','PA']
    matfiles={part:'mech-mat-%s_ACTIVE.inp'%part for part in parts}
    matfiles['PA']='mech-mat-PASSIVE.inp'
    for part in parts:
        table_name='j'+part
        c.execute('drop table if exists %s;'%table_name)
        c.execute('create table {0}(jID int, {1});'\
                  .format(table_name,sql_create_table))
    c.execute('SELECT jID, jName FROM jData;')
    jobs_in_jData=c.fetchall()
    jobs={name:ID for (ID,name) in jobs_in_jData}
    for name,ID in jobs.items():
        lr_dict=read_lr(name,rootf)
        for part, matfile in matfiles.items():
            try:
                t_name='j'+part
                mat_params=read_mat(name,matfile,rootf)+[lr_dict.pop(part,None)]
                sql_command='INSERT INTO {0}(jID,{1}) VALUES ({2}{3});'\
                    .format(t_name,sql_fill_table,ID,',?'*len(mat_params))
                c.execute(sql_command,mat_params)
            except Exception as err:
                print(err)
                print('Error when working with {0} on job {1}:{2}'.format(\
                      part,ID,name))

def read_mat(name,matfile,rootf='D:/users/eta2/hCxBvf'):
    fullpath=rootf+'/'+name+'/'+matfile
    mat_params=[]
    try:
        with open(fullpath) as matfile:
            lines=matfile.readlines()
        mat_params=','.join(lines[4:7]).split(',')
        mat_params=[float(x) for x in mat_params if len(x.strip())>0]
    except Exception as err:
        print(err)
    return mat_params
        

def read_lr(name,rootf='D:/users/eta2/hCxBvf'):
    fullpath=rootf+'/'+name+'/mech-mat-RV_ACTIVE.inp'
    lr_dict={}
    try:
        with open(fullpath) as RVfile:
            raw=RVfile.read()
        start=raw.find('*Initial')
        lines=raw[start:].strip().splitlines()[1:]
        for line in lines:
            if 'Ventricles' in line and 'ALL-NODES' in line:
                lr_dict['LV']=float(line.split(',')[-1])
                lr_dict['RV']=float(line.split(',')[-1])
                lr_dict['PA']=float(line.split(',')[-1])
            elif 'R_A' in line:
                lr_dict['RA']=float(line.split(',')[-1])
            elif 'L_A' in line:
                lr_dict['LA']=float(line.split(',')[-1])
            elif 'Ventricles' in line and 'LV' in line:
                lr_dict['LV']=float(line.split(',')[-1])
            elif 'Ventricles' in line and 'RV' in line:
                lr_dict['RV']=float(line.split(',')[-1])
    except Exception as err:
        print(err)
        print('Problem with %s material when retrieving lr')
    if not lr_dict:
        print("We couldn't get the lr values for %s"%name)
    elif 1<len(lr_dict)<4:
        print('We could only find lr values of {0} for {1}'\
              .format(str(list(lr_dict.keys())),name))
    return lr_dict

def read_PV_result(file):
    result=pd.read_csv(file)
    clean=result.drop_duplicates('X')
    return clean

def read_facts(name,rootf='D:/users/eta2/hCxBvf'):
    # Read start and end times from log file
    dates=[]
    errors=[]
    try:
        with open(rootf+'/'+name+'/'+name+'.log','r') as logfile:
            for line in logfile:
                line=line.strip()
                try:
                    date=datetime.strptime(line,"%a %d %b %Y %I:%M:%S %p EDT")
                    dates.append(date)
                except:
                    pass
    except Exception as err_log:
        print(err_log)
        dates=[datetime.fromordinal(1)]*2
        errors.append(err_log)
    duration=(dates[-1]-dates[0]).total_seconds()/3600
    # Read machine from .dat file
    try:
        with open(rootf+'/'+name+'/'+name+'.dat','r') as datfile:
            raw=datfile.read(1000)
        raw=raw.split(' machine ')
        raw=raw[1].splitlines()
        machine=raw[0].strip()
    except Exception as err_dat:
        print(err_dat)
        machine='error'
        errors.append(err_dat)
    # Read a lotta things from .sta file
    try:
        with open(rootf+'/'+name+'/'+name+'.sta','r') as stafile:
            raw=stafile.read()
        raw=raw.split('Domain level parallelization will be used with ',1)
        raw=raw[1].split(' processors.',1)
        cores=int(raw[0])
        raw=raw[1].split('INSTANCE WITH CRITICAL ELEMENT:')
        last_line=raw[-2].split()
        sec_computed=float(last_line[-7])
        duration2=last_line[-6]
    except Exception as err_sta:
        print(err_sta)
        errors.append(err_sta)
    
    # Read from job file, inp
    try:
        with open(rootf+'/'+name+'/'+name+'.inp','r') as jobfile:
            raw=jobfile.read()
        raw=raw.split('** STEP: ')
        pre_steps=raw[0]
        steps=raw[1:]
        # Read pre-load step
        prel_dur=steps[0].find('*Dynamic, Explicit')
        prel_dur=steps[0][prel_dur:].splitlines()
        prel_dur=float(prel_dur[1].split()[-1])
    except Exception as err_inp:
        print(err_inp)
        errors.append(err_inp)
    
    return {'start':str(dates[0]),'end':str(dates[-1]),\
            'duration':duration,'duration2':duration2,\
            'machine':machine,'cores':cores,'sec_computed':sec_computed,\
            'steps':len(steps),'prel_duration':prel_dur}


#if __name__ == "__main__":
if True:
    step0=time.clock()
    db,c=create_DB('dbwithhash.db')
    step1=time.clock()
    print('%.4g'%(step1-step0)+'s to create and hash names')
    
    c.execute('SELECT count(*) FROM jData;')
    print('%i jobs in the database'%c.fetchall()[0][0])
    
    step1=time.clock()
    insert_PV(c)
    db.commit()
    step2=time.clock()
    print('%.4g'%(step2-step1)+'s to insert PV')
    
    step1=time.clock()
    insert_facts(c)
    db.commit()
    step2=time.clock()
    print('%.4g'%(step2-step1)+'s to insert Facts')
    
    step1=time.clock()
    insert_materials(c)
    db.commit()
    step2=time.clock()
    print('%.4g'%(step2-step1)+'s to insert Materials')
    
    print('%.4g'%(step2-step0)+'s Total')
    