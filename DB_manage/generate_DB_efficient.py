# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 15:14:31 2016

@author: eta2
"""

import os
import sqlite3 as sql
import pandas as pd
import numpy as np
import time
from datetime import datetime
from hashlib import md5
from tqdm import tqdm

def hashstr(name):
    return md5(name.lower().encode()).hexdigest()[-6:].upper()

def create_DB(db_file,rootf='D:/users/eta2/hCxBvf',ODBsf='ODBs'):
    db=sql.connect(rootf+'/'+db_file)
    c=db.cursor()
    c.execute('drop table if exists jData;')
    c.execute('''create table jData(jID int primary key, jName text, jHash text, 
                 duration real, duration2 text, start text, end text, 
                 machine text, cores int, steps int, prel_duration real,
                 sec_computed real, 
                 C1 real, C2 real, C3 real, C4 real, C5 real, C6 real, C7 real,
                 CT real);''')
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
    #create jPV table
    c.execute('drop table if exists jPV;')
    c.execute('''create table jPV(jID int, X real,
              P1 real, P2 real, P3 real, P4 real, P5 real, P6 real, P7 real,
              V1 real, V2 real, V3 real, V4 real, V5 real, V6 real, V7 real
              );''')
    #create five material tables
    materials=['a','b','af','bf','a_s','bs','afs','bfs','D',\
               't0','m','b_tr','l0','B_ECa','Ca0max','Ca0','Tmax',\
               'Frac_Lat','ip','lr']
    mat_sql_create_table=' real, '.join(materials)+' real'
    parts=['RA','RV','LA','LV','PA']
    for part in parts:
        table_name='j'+part
        c.execute('drop table if exists %s;'%table_name)
        c.execute('create table {0}(jID int primary key, {1});'\
                  .format(table_name,mat_sql_create_table))
    #create jHem
    hemod_params=['SBP','DBP','MAP','MAPi','RVSP','RVDP','PASP','PADP','MPAP',\
           'MPAPi','RAP','CVP','LAP','PAOP','SV','RVSV','CO','SVR','PVR',\
           'LVSW','RVSW','EF','RVEF','MAX_LV_P','MAX_RV_P','MAX_LV_V',\
           'MAX_RV_V','MIN_LV_P','MIN_RV_P','MIN_LV_V','MIN_RV_V','LV_P_CONV']
    hem_sql_create_table=' real, '.join(hemod_params)+' real'
    c.execute('drop table if exists jHem;')
    c.execute('create table jHem(jID int primary key, {0});'\
              .format(hem_sql_create_table))
    #create jR table
    jR_cols=["Rm%i"%i for i in range(1,8)]+\
             ["V%i"%i for i in range(1,8)]+\
              ["R%i"%i for i in range(1,8)]
    jR_sql_create_table=' real, '.join(jR_cols)+' real'
    c.execute('drop table if exists jR;')
    c.execute('create table jR(jID int primary key, {0});'\
              .format(jR_sql_create_table))
    db.commit()
    return db,c

def fill_DB(c,rootf='D:/users/eta2/hCxBvf',resultsf='results'):
    #loop job by job
    c.execute('SELECT jID, jName FROM jData;')
    jobs_in_jData=c.fetchall()
    jobs={name:ID for (ID,name) in jobs_in_jData}
    materials=['a','b','af','bf','a_s','bs','afs','bfs','D',\
               't0','m','b_tr','l0','B_ECa','Ca0max','Ca0','Tmax',\
               'Frac_Lat','ip','lr']
    mat_sql_fill_table=','.join(materials)
    
    for name,ID in tqdm(jobs.items()):
#    for name,ID in jobs.items():
        #insert_PV:
        XPV=read_PV_result(rootf+'/'+resultsf+'/'+name+'_PV.csv')
        columns=['jID']+list(XPV.columns)
        c.executemany('INSERT INTO jPV('+','.join(columns)+') VALUES ({0}{1});'\
                .format(ID,',?'*15),XPV.as_matrix())
        # get miscellanous data, it will be inserted later:
        with open(rootf+'/'+name+'/'+name+'.inp','r') as jobfile:
            jobinp=jobfile.read()[15982640:]
        dictio=read_facts(name,jobinp=jobinp,rootf=rootf)
#        sql_update_set=['%s=?'%key for key in dictio.keys()]
#        c.execute('UPDATE jData SET {1} WHERE jID={0};'\
#            .format(ID,','.join(sql_update_set)),tuple(dictio.values()))
        #insert materials:
        parts=['RA','RV','LA','LV','PA']
        matfiles={part:'mech-mat-%s_ACTIVE.inp'%part for part in parts}
        matfiles['PA']='mech-mat-PASSIVE.inp'
        lr_dict=read_lr(name,rootf)
        for part, matfile in matfiles.items():
            t_name='j'+part
            mat_params=read_mat(name,matfile,rootf)+[lr_dict.pop(part,None)]
            sql_command='INSERT INTO {0}(jID,{1}) VALUES ({2}{3});'\
                .format(t_name,mat_sql_fill_table,ID,',?'*len(mat_params))
            c.execute(sql_command,mat_params)
        # insert hem params
        # we have to slice XPV for the last beat and also for the previous one
        sec_computed=dictio['sec_computed']
        tPV=XPV[XPV.X>=sec_computed-1]
        t=tPV.X-sec_computed+1
        VEN_P,RA_P,RV_P,PUL_P,LA_P,LV_P,ART_P='P1','P2','P3','P4','P5','P6','P7'
        VEN_V,RA_V,RV_V,PUL_V,LA_V,LV_V,ART_V='V1','V2','V3','V4','V5','V6','V7'
        # h_pars === hemodynamic parameters ; cf=== conversion factor
        h_pars={}
        #Systolic and diastolic blood pressure (arterial)
        h_pars['SBP']=tPV[ART_P].max()
        h_pars['DBP']=tPV[ART_P].min()
        # Mean arterial pressure, lab formula and real integrated formula
        h_pars['MAP']=(h_pars['SBP']+2*h_pars['DBP'])/3
        h_pars['MAPi']=np.trapz(tPV[ART_P],t)/(t.max()-t.min())
        #Systolic and diastolic RV pressure
        h_pars['RVSP']=tPV[RV_P].max()
        h_pars['RVDP']=tPV[RV_P].min()
        #Systolic, diastolic, and mean pulmonary arterial pressure (and integrated)
        h_pars['PASP']=tPV[PUL_P].max()
        h_pars['PADP']=tPV[PUL_P].min()
        h_pars['MPAP']=(h_pars['PASP']+2*h_pars['PADP'])/3
        h_pars['MPAPi']=np.trapz(tPV[PUL_P],t)/(t.max()-t.min())
        #Mean right and left atrial and venous pressure
        h_pars['RAP']=np.trapz(tPV[RA_P],t)/(t.max()-t.min())
        h_pars['CVP']=np.trapz(tPV[VEN_P],t)/(t.max()-t.min())
        h_pars['LAP']=np.trapz(tPV[LA_P],t)/(t.max()-t.min())
        h_pars['PAOP']=h_pars['LAP']
        #Cardiac output and Stroke volume
        HR=60 #This will have to be a function of each beat in the future
        h_pars['SV']=(tPV[LV_V].max()-tPV[LV_V].min())
        h_pars['RVSV']=(tPV[RV_V].max()-tPV[RV_V].min())
        h_pars['CO']=HR*h_pars['SV']/1000
        #Systemic and pulmonary Vascular Resistance
        h_pars['SVR']=80*(h_pars['MAP']-h_pars['RAP'])/h_pars['CO']
        h_pars['PVR']=80*(h_pars['MPAP']-h_pars['PAOP'])/h_pars['CO']
        #Stroke work
        h_pars['LVSW']=np.trapz(tPV[LV_P],tPV[LV_V])*0.133322
        h_pars['RVSW']=np.trapz(tPV[RV_P],tPV[RV_V])*0.133322
        #Ejection Fraction
        h_pars['EF']=100*h_pars['SV']/(tPV[LV_V].max())
        h_pars['RVEF']=100*h_pars['RVSV']/(tPV[RV_V].max())
        #Other interesting params:
        h_pars['MAX_LV_P']=tPV[LV_P].max()
        h_pars['MAX_RV_P']=tPV[RV_P].max()
        h_pars['MAX_LV_V']=tPV[LV_V].max()
        h_pars['MAX_RV_V']=tPV[RV_V].max()
        h_pars['MIN_LV_P']=tPV[LV_P].min()
        h_pars['MIN_RV_P']=tPV[RV_P].min()
        h_pars['MIN_LV_V']=tPV[LV_V].min()
        h_pars['MIN_RV_V']=tPV[RV_V].min()
        #LV P Converged?
        prev_beat=XPV[(XPV.X>=sec_computed-2) & (XPV.X<=sec_computed-1)]
#        prev_beat=prev_beat[prev_beat['X']<=sec_computed-1]
        h_pars['LV_P_CONV']=100*(tPV[LV_P].max()-prev_beat[LV_P].max())/prev_beat[LV_P].max()
        columns=['jID']+list(h_pars.keys())
        c.execute(\
            'INSERT INTO jHem({2}) VALUES ({0}{1});'\
            .format(ID,',?'*len(h_pars),','.join(columns)),\
            tuple(h_pars.values()))
        # insert Rs
        Rs=readR(jobinp=jobinp)
        columns=['jID']+list(Rs.keys())
        c.execute(\
            'INSERT INTO jR({2}) VALUES ({0}{1});'\
            .format(ID,',?'*len(Rs),','.join(columns)),\
            tuple(Rs.values()))
        # compute convergence as distance between start and end in PVloop of last beat
        P=tPV.loc[:,'P1':'P7']
        V=tPV.loc[:,'V1':'V7']
        P_scal=(P-P.min())/(P.max()-P.min())
        V_scal=(V-V.min())/(V.max()-V.min())
        conv_array=(P_scal.iloc[-1]-P_scal.iloc[0]).values**2 + (V_scal.iloc[-1]-V_scal.iloc[0]).values**2
        cdict={"C%i"%(i+1) : val for i,val in enumerate(conv_array)}
        cdict['CT']=conv_array.mean()
        dictio.update(cdict)
        sql_update_set=['%s=?'%key for key in dictio.keys()]
        c.execute('UPDATE jData SET {1} WHERE jID={0};'\
            .format(ID,','.join(sql_update_set)),tuple(dictio.values()))
        
        

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
    P=clean[['P1','P2','P3','P4','P5','P6','P7']].values*7500
    V=clean[['V1','V2','V3','V4','V5','V6','V7']].values*0.001
    return pd.DataFrame(np.c_[clean['X'].values,P,V],columns=clean.columns)

def read_facts(name,jobinp,rootf='D:/users/eta2/hCxBvf'):
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
            raw=datfile.read(1024)
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
        jobinp=jobinp.split('** STEP: ')
        pre_steps=jobinp[0]
        steps=jobinp[1:]
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

def readR(jobinp):
    A=np.array([441.15,1722.2,434.9,434.9,1039.8,441.15,441.15])
    #from 0 to 7, se we can work using from 1 to 7, usual convention:
    V=np.zeros(8)
    ro=1.027e-9
    inplines=jobinp.splitlines()
    for i,line in enumerate(inplines):
        line=line.strip()
        if '*Fluid Exchange Property, name=Link-Aortic-V' in line:
            V[6]=float(inplines[i+1].split(',')[0])
        elif '*Fluid Exchange Property, name=Link-Body-R' in line:
            V[7]=float(inplines[i+1].split(',')[0])
        elif '*Fluid Exchange Property, name=Link-Mitral' in line:
            V[5]=float(inplines[i+1].split(',')[0])
        elif '*Fluid Exchange Property, name=Link-Pulmonary-R' in line:
            V[4]=float(inplines[i+1].split(',')[0])
        elif '*Fluid Exchange Property, name=Link-Pulmonary-V' in line:
            V[3]=float(inplines[i+1].split(',')[0])
        elif '*Fluid Exchange Property, name=Link-Tricuspid-V' in line:
            V[2]=float(inplines[i+1].split(',')[0])
        elif '*Fluid Exchange Property, name=Link-Venous-R' in line:
            V[1]=float(inplines[i+1].split(',')[0])
        if sum(V==0)==1:
            break
    V=V[1:]
    V_base=np.array([429.5,429.5,423.47,1751.03,2359.04,536.,59965.5])
    R=ro*V/A
    # On the next line we are making the assumption that the A hasn't been modified
    Rm=V/V_base
    Vdict={"V%i"%i:val for i,val in enumerate(V,start=1)}
    Rdict={"R%i"%i:val for i,val in enumerate(R,start=1)}
    Rmdict={"Rm%i"%i:val for i,val in enumerate(Rm,start=1)}
    Rdict.update(Vdict)
    Rdict.update(Rmdict)
    return Rdict

#if __name__ == "__main__":
if True:
    rootf='D:/users/eta2/hCxBvf'
    step0=time.clock()
    db,c=create_DB('dbPVhashhemoRs-fast-mmHg-cm3-new.db',rootf=rootf)
    step1=time.clock()
    print('%.4g'%(step1-step0)+'s to create the DB with IDs, names and hashes')
    
    c.execute('SELECT count(*) FROM jData;')
    print('%i jobs in the database'%c.fetchall()[0][0])
    
    step1=time.clock()
    fill_DB(c,rootf=rootf,resultsf='results')
    db.commit()
    step2=time.clock()
    print('%.4g'%(step2-step1)+'s to fill DB')

    db.close()
    
    print('%.4g'%(step2-step0)+'s Total')
