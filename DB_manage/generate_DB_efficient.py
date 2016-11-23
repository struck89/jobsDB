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
import json
from datetime import datetime
from hashlib import md5
from tqdm import tqdm

def hashstr(name):
    return md5(name.lower().encode()).hexdigest()[-6:].upper()

def create_DB(db_file,rootf='D:/users/eta2/hCxBvf',ODBsf='ODBs',howmany=-1):
    db=sql.connect(os.path.join(rootf,db_file))
    c=db.cursor()
    c.execute('drop table if exists jData;')
    c.execute('''create table jData(jID int primary key, jName text, jHash text, 
                 duration real, duration2 text, start text, end text, 
                 machine text, cores int, steps int, prel_duration real,
                 sec_computed real, description text);''')
    #now get all jobs in ./ODBs/ that have a folder in ./ with the same name
    ODBs_cand=os.listdir(os.path.join(rootf,ODBsf))
    ODBs_cand=[name[:-4] for name in ODBs_cand if name[-3:].lower()=='odb']
    ODBs=[folder for folder in os.listdir(rootf) if \
          (folder in ODBs_cand and \
           os.path.isdir(os.path.join(rootf,folder)))]
    ODBs.sort()
    if howmany>-1:
        ODBs=ODBs[:howmany]
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
           'MAX_RV_V','MIN_LV_P','MIN_RV_P','MIN_LV_V','MIN_RV_V','LV_P_CONV',
           'Total_Vol']
    hem_sql_create_table=' real, '.join(hemod_params)+' real'
    c.execute('drop table if exists jHem;')
    c.execute('create table jHem(jID int primary key, {0});'\
              .format(hem_sql_create_table))
    #create jR table
    jR_cols=["R%im"%i for i in range(1,8)]+\
             ["V%i"%i for i in range(1,8)]+\
              ["R%i"%i for i in range(1,8)]
    jR_sql_create_table=' real, '.join(jR_cols)+' real'
    c.execute('drop table if exists jR;')
    c.execute('create table jR(jID int primary key, {0});'\
              .format(jR_sql_create_table))
    c.execute('drop table if exists jConv;')
    c.execute('''create table jConv(jID int primary key, C1 real, C2 real, 
                 C3 real, C4 real, C5 real, C6 real, C7 real, CT real, sqP1 real,
                 sqP2 real, sqP3 real, sqP4 real, sqP5 real, sqP6 real, sqP7 real,
                 sqV1 real, sqV2 real, sqV3 real, sqV4 real, sqV5 real, sqV6 real,
                 sqV7 real, 
                 dfPmax1 real, dfPmax2 real, dfPmax3 real, dfPmax4 real,
                 dfPmax5 real, dfPmax6 real, dfPmax7 real,
                 dfVmax1 real, dfVmax2 real, dfVmax3 real, dfVmax4 real,
                 dfVmax5 real, dfVmax6 real, dfVmax7 real,
                 dfPmin1 real, dfPmin2 real, dfPmin3 real, dfPmin4 real,
                 dfPmin5 real, dfPmin6 real, dfPmin7 real,
                 dfVmin1 real, dfVmin2 real, dfVmin3 real, dfVmin4 real,
                 dfVmin5 real, dfVmin6 real, dfVmin7 real);''')
    c.execute('drop table if exists jC;')
    c.execute('''create table jC(jID int primary key, VEN_K real, PUL_K real, 
                 ART_K real);''')
    db.commit()
    return db,c

def fill_DB(c,rootf='D:/users/eta2/hCxBvf',resultsf='results_mmHgml'):
    #loop job by job
    c.execute('SELECT jID, jName, jHash FROM jData;')
    jobs_in_jData=c.fetchall()
    jobs={name:(ID,jHash) for (ID,name,jHash) in jobs_in_jData}
    materials=['a','b','af','bf','a_s','bs','afs','bfs','D',\
               't0','m','b_tr','l0','B_ECa','Ca0max','Ca0','Tmax',\
               'Frac_Lat','ip','lr']
    #the following constant is meant to fix the problems that occur with float precision.
    err_corr=1.0001
    # the version of the json file this script will produce. If different from
    # the one in a job's folder, the json will be generated again
    json_v=1
    for name,(ID,jHash) in tqdm(jobs.items()):
#    for name,ID in jobs.items():
        has_updated_json=False
        jsonpath=os.path.join(rootf,name,'data.json')
        if os.path.isfile(jsonpath):
            try:
                with open(jsonpath) as f:
                    jsondata=json.load(f)
                json_recorded_v=jsondata.pop('json_v',0)
            except:
                json_recorded_v=0
            if json_v==json_recorded_v:
                has_updated_json=True
        XPV=read_PV_result(os.path.join(rootf,resultsf,name+'_mmHgml.csv'))
        if has_updated_json:
            jData=jsondata.pop('jData')
            jHem=jsondata.pop('jHem')
            jR=jsondata.pop('jR')
            jC=jsondata.pop('jC')
            jMat=jsondata.pop('jMat')
            jConv=jsondata.pop('jConv')
        else:
            # jData
            jobinppath=os.path.join(rootf,name,name+'.inp')
            with open(jobinppath,'r') as jobfile:
                jobinp=jobfile.read()[15000000:]
            jData=read_facts(name,jobinp=jobinp,rootf=rootf)
            jData['jHash']=jHash
            jData['jName']=name
            # jHem
            # we have to slice XPV for the last beat and also for the previous one
            sec_computed=jData['sec_computed']
            tPV=XPV[XPV.X>=sec_computed-1*err_corr]
            t=tPV.X-sec_computed+1
            VEN_P,RA_P,RV_P,PUL_P,LA_P,LV_P,ART_P='P1','P2','P3','P4','P5','P6','P7'
            VEN_V,RA_V,RV_V,PUL_V,LA_V,LV_V,ART_V='V1','V2','V3','V4','V5','V6','V7'
            # jHem === hemodynamic parameters ; cf=== conversion factor
            jHem={}
            #Systolic and diastolic blood pressure (arterial)
            jHem['SBP']=tPV[ART_P].max()
            jHem['DBP']=tPV[ART_P].min()
            # Mean arterial pressure, lab formula and real integrated formula
            jHem['MAP']=(jHem['SBP']+2*jHem['DBP'])/3
            jHem['MAPi']=np.trapz(tPV[ART_P],t)/(t.max()-t.min())
            #Systolic and diastolic RV pressure
            jHem['RVSP']=tPV[RV_P].max()
            jHem['RVDP']=tPV[RV_P].min()
            #Systolic, diastolic, and mean pulmonary arterial pressure (and integrated)
            jHem['PASP']=tPV[PUL_P].max()
            jHem['PADP']=tPV[PUL_P].min()
            jHem['MPAP']=(jHem['PASP']+2*jHem['PADP'])/3
            jHem['MPAPi']=np.trapz(tPV[PUL_P],t)/(t.max()-t.min())
            #Mean right and left atrial and venous pressure
            jHem['RAP']=np.trapz(tPV[RA_P],t)/(t.max()-t.min())
            jHem['CVP']=np.trapz(tPV[VEN_P],t)/(t.max()-t.min())
            jHem['LAP']=np.trapz(tPV[LA_P],t)/(t.max()-t.min())
            jHem['PAOP']=jHem['LAP']
            #Cardiac output and Stroke volume
            HR=60 #This will have to be a function of each beat in the future
            jHem['SV']=(tPV[LV_V].max()-tPV[LV_V].min())
            jHem['RVSV']=(tPV[RV_V].max()-tPV[RV_V].min())
            jHem['CO']=HR*jHem['SV']/1000
            #Systemic and pulmonary Vascular Resistance
            jHem['SVR']=80*(jHem['MAP']-jHem['RAP'])/jHem['CO']
            jHem['PVR']=80*(jHem['MPAP']-jHem['PAOP'])/jHem['CO']
            #Stroke work
            jHem['LVSW']=np.trapz(tPV[LV_P],tPV[LV_V])*0.133322
            jHem['RVSW']=np.trapz(tPV[RV_P],tPV[RV_V])*0.133322
            #Ejection Fraction
            jHem['EF']=100*jHem['SV']/(tPV[LV_V].max())
            jHem['RVEF']=100*jHem['RVSV']/(tPV[RV_V].max())
            #Other interesting params:
            jHem['MAX_LV_P']=tPV[LV_P].max()
            jHem['MAX_RV_P']=tPV[RV_P].max()
            jHem['MAX_LV_V']=tPV[LV_V].max()
            jHem['MAX_RV_V']=tPV[RV_V].max()
            jHem['MIN_LV_P']=tPV[LV_P].min()
            jHem['MIN_RV_P']=tPV[RV_P].min()
            jHem['MIN_LV_V']=tPV[LV_V].min()
            jHem['MIN_RV_V']=tPV[RV_V].min()
            #LV P Converged?
            prev_beat=XPV[(XPV.X>=sec_computed-2*err_corr) & (XPV.X<=sec_computed-1/err_corr)]
            jHem['LV_P_CONV']=100*(tPV[LV_P].max()-prev_beat[LV_P].max())/prev_beat[LV_P].max()
            jHem['Total_Vol']=tPV.iloc[-1,-7:].sum()
            
            # jConv
            P=tPV.loc[:,'P1':'P7']
            V=tPV.loc[:,'V1':'V7']
            P_scal=(P-P.min())/(P.max()-P.min())
            V_scal=(V-V.min())/(V.max()-V.min())
            conv_array=(P_scal.iloc[-1]-P_scal.iloc[0]).values**2 + (V_scal.iloc[-1]-V_scal.iloc[0]).values**2
            conv_array=np.sqrt(conv_array)
            jConv={"C%i"%(i+1) : val for i,val in enumerate(conv_array)}
            jConv['CT']=conv_array.mean()
            # changing the index allows us to substract the values later on
            P_pre=prev_beat.loc[:,'P1':'P7'].set_index(P.index)
            V_pre=prev_beat.loc[:,'V1':'V7'].set_index(V.index)
            P_sqerr=((P-P_pre)**2).sum()
            V_sqerr=((V-V_pre)**2).sum()
            sqPdict={"sqP%i"%(i+1) : val for i,val in enumerate(P_sqerr)}
            sqVdict={"sqV%i"%(i+1) : val for i,val in enumerate(V_sqerr)}
            dfPmax=P.max()-P_pre.max()
            dfVmax=V.max()-V_pre.max()
            dfPmin=P.min()-P_pre.min()
            dfVmin=V.min()-V_pre.min()
            dfPmaxdict={"dfPmax%i"%(i+1) : val for i,val in enumerate(dfPmax)}
            dfVmaxdict={"dfVmax%i"%(i+1) : val for i,val in enumerate(dfVmax)}
            dfPmindict={"dfPmin%i"%(i+1) : val for i,val in enumerate(dfPmin)}
            dfVmindict={"dfVmin%i"%(i+1) : val for i,val in enumerate(dfVmin)}
            jConv.update(sqPdict)
            jConv.update(sqVdict)
            jConv.update(dfPmaxdict)
            jConv.update(dfVmaxdict)
            jConv.update(dfPmindict)
            jConv.update(dfVmindict)
            
            # jR and jC
            jR,jC=readRC(jobinp=jobinp)
            
            # jMat
            parts=['RA','RV','LA','LV','PA']
            matfiles={part:'mech-mat-%s_ACTIVE.inp'%part for part in parts}
            matfiles['PA']='mech-mat-PASSIVE.inp'
            lr_dict=read_lr(name,rootf)
            jMat={}
            for part, matfile in matfiles.items():
                t_name='j'+part
                mat_params=read_mat(name,matfile,rootf)+[lr_dict.pop(part,None)]
#                sql_command='INSERT INTO {0}(jID,{1}) VALUES ({2}{3});'\
#                    .format(t_name,mat_sql_fill_table,ID,',?'*len(mat_params))
#                c.execute(sql_command,mat_params)
                jMat[t_name]=dict(zip(materials,mat_params))
            jsondata={'json_v':json_v,
                      'jData':jData,
                      'jHem':jHem,
                      'jR':jR,
                      'jC':jC,
                      'jMat':jMat,
                      'jConv':jConv}
            with open(jsonpath,'w') as f:
                json.dump(jsondata,f,indent=4,sort_keys=True)         

        #insert_PV:
        jPVcolumns=['jID']+list(XPV.columns)
        c.executemany('INSERT INTO jPV('+','.join(jPVcolumns)+') VALUES ({0}{1});'\
                .format(ID,',?'*15),XPV.values)
        
        sql_update_set=['%s=?'%key for key in jData.keys()]
        c.execute('UPDATE jData SET {1} WHERE jID={0};'\
            .format(ID,','.join(sql_update_set)),tuple(jData.values()))
        
        #insert materials:
        for jpartname, jpartdict in jMat.items():
            jpartcolumns=['jID']+list(jpartdict.keys())
            c.execute(\
                'INSERT INTO {3}({2}) VALUES ({0}{1});'\
                .format(ID,',?'*len(jpartdict),','.join(jpartcolumns),jpartname),\
                tuple(jpartdict.values()))
        
        # insert hem params
        jHemcolumns=['jID']+list(jHem.keys())
        c.execute(\
            'INSERT INTO jHem({2}) VALUES ({0}{1});'\
            .format(ID,',?'*len(jHem),','.join(jHemcolumns)),\
            tuple(jHem.values()))
        
        # insert Rs and Cs
        jRcolumns=['jID']+list(jR.keys())
        c.execute(\
            'INSERT INTO jR({2}) VALUES ({0}{1});'\
            .format(ID,',?'*len(jR),','.join(jRcolumns)),\
            tuple(jR.values()))
        
        jCcolumns=['jID']+list(jC.keys())
        c.execute(\
            'INSERT INTO jC({2}) VALUES ({0}{1});'\
            .format(ID,',?'*len(jC),','.join(jCcolumns)),\
            tuple(jC.values()))
        
        # compute convergence as distance between start and end in PVloop of last beat
        jConvcolumns=['jID']+list(jConv.keys())
        c.execute(\
            'INSERT INTO jConv({2}) VALUES ({0}{1});'\
            .format(ID,',?'*len(jConv),','.join(jConvcolumns)),\
            tuple(jConv.values()))

def read_mat(name,matfile,rootf='D:/users/eta2/hCxBvf'):
    fullpath=os.path.join(rootf,name,matfile)
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
    fullpath=os.path.join(rootf,name,'mech-mat-RV_ACTIVE.inp')
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
#    P=clean.loc[:,'P1':'P7'].values*7500
#    V=clean.loc[:,'V1':'V7'].values*0.001
#    return pd.DataFrame(np.c_[clean.X.values,P,V],columns=clean.columns)

def read_facts(name,jobinp,rootf='D:/users/eta2/hCxBvf'):
    # Read start and end times from log file
    dates=[]
    facts={}
    try:
        logfilepath=os.path.join(rootf,name,name+'.log')
        with open(logfilepath,'r') as logfile:
            for line in logfile:
                line=line.strip().replace('EST','EDT')
                try:
                    date=datetime.strptime(line,"%a %d %b %Y %I:%M:%S %p EDT")
                    dates.append(date)
                except:
                    pass
        facts['duration']=(dates[-1]-dates[0]).total_seconds()/3600
        facts['start']=str(dates[0])
        facts['end']=str(dates[-1])
    except Exception as err_log:
        print(err_log)
        print('Error with dates and or logfile with job %s'%name)
    # Read machine from .dat file
    try:
        datfilepath=os.path.join(rootf,name,name+'.dat')
        with open(datfilepath,'r') as datfile:
            raw=datfile.read(1024)
        raw=raw.split(' machine ')
        raw=raw[1].splitlines()
        facts['machine']=raw[0].strip()
    except Exception as err_dat:
        print(err_dat)

    # Read a lotta things from .sta file
    try:
        stafilepath=os.path.join(rootf,name,name+'.sta')
        with open(stafilepath,'r') as stafile:
            raw=stafile.read()
        raw=raw.split('Domain level parallelization will be used with ',1)
        raw=raw[1].split(' processors.',1)
        facts['cores']=int(raw[0])
        raw=raw[1].split('INSTANCE WITH CRITICAL ELEMENT:')
        last_line=raw[-2].split()
        facts['sec_computed']=float(last_line[-7])
        facts['duration2']=last_line[-6]
    except Exception as err_sta:
        print(err_sta)

    # Process job file, inp
    try:
        jobinp=jobinp.split('** STEP: ')
        pre_steps=jobinp[0]
        steps=jobinp[1:]
        # Read pre-load step
        prel_dur=steps[0].find('*Dynamic, Explicit')
        prel_dur=steps[0][prel_dur:].splitlines()
        facts['steps']=len(steps)
        facts['prel_duration']=float(prel_dur[1].split()[-1])
    except Exception as err_inp:
        print(err_inp)

    # Read job description
    try:
        descfilepath=os.path.join(rootf,name,'description.txt')
        with open(descfilepath,'r') as descrfile:
            raw=descrfile.read()
        facts['description']=raw.strip()
    except Exception as err_inp:
        pass
    
    return facts

def readRC(jobinp):
    A=np.array([441.15,1722.2,434.9,434.9,1039.8,441.15,441.15])
    #from 0 to 7, se we can work using from 1 to 7, usual convention:
    V=np.zeros(8)
    ro=1.027e-9
    Cdict={}
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
        elif 'Stiffness-Arterial' in line:
            if 'Elasticity' in inplines[i+1]:
                Cdict['ART_K']=float(inplines[i+2].split(',')[0])
        elif 'Stiffness-Venous' in line:
            if 'Elasticity' in inplines[i+1]:
                Cdict['VEN_K']=float(inplines[i+2].split(',')[0])
        elif 'Stiffness-Pulmonary' in line:
            if 'Elasticity' in inplines[i+1]:
                Cdict['PUL_K']=float(inplines[i+2].split(',')[0])
        if len(Cdict)==3 and sum(V==0)==1:
            break
    V=V[1:]
    V_base=np.array([429.5,429.5,423.47,1751.03,2359.04,536.,59965.5])
    R=ro*V/A
    # On the next line we are making the assumption that the A hasn't been modified
    Rm=V/V_base
    Vdict={"V%i"%i:val for i,val in enumerate(V,start=1)}
    Rdict={"R%i"%i:val for i,val in enumerate(R,start=1)}
    Rmdict={"R%im"%i:val for i,val in enumerate(Rm,start=1)}
    Rdict.update(Vdict)
    Rdict.update(Rmdict)
    return Rdict,Cdict

def gen_mmHgml(rootf='D:/users/eta2/hCxBvf'):
    res_files_MPa=os.listdir(os.path.join(rootf,'results'))
    res_files_MPa=[name[:-7] for name in res_files_MPa if name[-7:]=='_PV.csv']
    
    res_files_mmHg=os.listdir(os.path.join(rootf,'results_mmHgml'))
    res_files_mmHg=[name[:-11] for name in res_files_mmHg if name[-11:]=='_mmHgml.csv']
    
    files_to_process=[name for name in res_files_MPa if name not in res_files_mmHg]
    
    for jname in files_to_process:
        full_addr_in=os.path.join(rootf,'results',jname+'_PV.csv')
        full_addr_out=os.path.join(rootf,'results_mmHgml',jname+'_mmHgml.csv')
        
        df=pd.read_csv(full_addr_in)
        df.loc[:,'P1':'P7']=df.loc[:,'P1':'P7'].values*7500
        df.loc[:,'V1':'V7']=df.loc[:,'V1':'V7'].values*0.001
    
        df.to_csv(path_or_buf=full_addr_out,float_format="%.6g",index=False)

#if __name__ == "__main__":
if True:
    rootf=os.getcwd()
    gen_mmHgml(rootf=rootf)
    step0=time.clock()
    db,c=create_DB('dbPVhashhemoRs-fast-mmHg-cm3-sqerr-descr.db',rootf=rootf,howmany=-1)
    step1=time.clock()
    print('%.4g'%(step1-step0)+'s to create the DB with IDs, names and hashes')
    
    c.execute('SELECT count(*) FROM jData;')
    print('%i jobs in the database'%c.fetchall()[0][0])
    
    step1=time.clock()
    try:
        fill_DB(c,rootf=rootf,resultsf='results_mmHgml')
    except BaseException as err:
        db.close()
        raise err
    db.commit()
    step2=time.clock()
    print('%.4g'%(step2-step1)+'s to fill DB')

    db.close()
    
    print('%.4g'%(step2-step0)+'s Total')
