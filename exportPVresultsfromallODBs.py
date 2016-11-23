# -*- coding: utf-8 -*-
#"""
#This file can only be run by Abaqus as a python script
# It can be run by running >'localabaq.bat cae nogui=exportPVresultsfromallODBs.py'
#"""

import visualization
import os

rootf=os.getcwd()
# List of the weird names needed to access the history output data
coarse_v=[
'Fluid cavity pressure: PCAV PI: VENOUS_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity pressure: PCAV PI: R_ATRIUM-1 Node 10783 in NSET CAV-RP',
'Fluid cavity pressure: PCAV PI: rootAssembly Node 12 in NSET RV-RP',
'Fluid cavity pressure: PCAV PI: PULMONARY_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity pressure: PCAV PI: L_ATRIUM-1 Node 11692 in NSET CAV-RP',
'Fluid cavity pressure: PCAV PI: rootAssembly Node 11 in NSET LV-RP',
'Fluid cavity pressure: PCAV PI: ARTERIAL_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: VENOUS_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: R_ATRIUM-1 Node 10783 in NSET CAV-RP',
'Fluid cavity volume: CVOL PI: rootAssembly Node 12 in NSET RV-RP',
'Fluid cavity volume: CVOL PI: PULMONARY_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: L_ATRIUM-1 Node 11692 in NSET CAV-RP',
'Fluid cavity volume: CVOL PI: rootAssembly Node 11 in NSET LV-RP',
'Fluid cavity volume: CVOL PI: ARTERIAL_COMPLIANCE-1 Node 9 in NSET RP']

medium_v=[
'Fluid cavity pressure: PCAV PI: VENOUS_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity pressure: PCAV PI: R_ATRIUM-1 Node 18864 in NSET CAV-RP',
'Fluid cavity pressure: PCAV PI: rootAssembly Node 12 in NSET RV-RP',
'Fluid cavity pressure: PCAV PI: PULMONARY_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity pressure: PCAV PI: L_ATRIUM-1 Node 14650 in NSET CAV-RP',
'Fluid cavity pressure: PCAV PI: rootAssembly Node 11 in NSET LV-RP',
'Fluid cavity pressure: PCAV PI: ARTERIAL_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: VENOUS_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: R_ATRIUM-1 Node 18864 in NSET CAV-RP',
'Fluid cavity volume: CVOL PI: rootAssembly Node 12 in NSET RV-RP',
'Fluid cavity volume: CVOL PI: PULMONARY_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: L_ATRIUM-1 Node 14650 in NSET CAV-RP',
'Fluid cavity volume: CVOL PI: rootAssembly Node 11 in NSET LV-RP',
'Fluid cavity volume: CVOL PI: ARTERIAL_COMPLIANCE-1 Node 9 in NSET RP']

fine_v=[
'Fluid cavity pressure: PCAV PI: VENOUS_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity pressure: PCAV PI: R_ATRIUM-1 Node 27286 in NSET CAV-RP',
'Fluid cavity pressure: PCAV PI: rootAssembly Node 12 in NSET RV-RP',
'Fluid cavity pressure: PCAV PI: PULMONARY_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity pressure: PCAV PI: L_ATRIUM-1 Node 21766 in NSET CAV-RP',
'Fluid cavity pressure: PCAV PI: rootAssembly Node 11 in NSET LV-RP',
'Fluid cavity pressure: PCAV PI: ARTERIAL_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: VENOUS_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: R_ATRIUM-1 Node 27286 in NSET CAV-RP',
'Fluid cavity volume: CVOL PI: rootAssembly Node 12 in NSET RV-RP',
'Fluid cavity volume: CVOL PI: PULMONARY_COMPLIANCE-1 Node 9 in NSET RP',
'Fluid cavity volume: CVOL PI: L_ATRIUM-1 Node 21766 in NSET CAV-RP',
'Fluid cavity volume: CVOL PI: rootAssembly Node 11 in NSET LV-RP',
'Fluid cavity volume: CVOL PI: ARTERIAL_COMPLIANCE-1 Node 9 in NSET RP']

#How are we going to call them instead

outVarNames=['P1','P2','P3','P4','P5','P6','P7',
            'V1','V2','V3','V4','V5','V6','V7']


#%%
# get ODBs in ODBs folder that are NOT in results folder:
folderRes=os.path.join(rootf,'results')
results=os.listdir(folderRes)
results=[filename[:-4] for filename in results]
folderODBs=os.path.join(rootf,'ODBs')
files=os.listdir(folderODBs)
odbs=[]
for odbwannabe in files:
    if (odbwannabe[-4:].lower()=='.odb') and \
       (odbwannabe[:-4]+'_PV' not in results):
        odbs.append(os.path.join(folderODBs,odbwannabe))
odbs.sort()

for odbfullpath in odbs:
    odbname=os.path.split(odbfullpath)[-1]
    g=open("processed_odbs.txt",'a')
    g.write("Processing %s.....\n"%odbfullpath)
    g.close()
    outfilename=odbname[:-4]+'_PV.csv'
    outfulladdress=os.path.join(rootf,'results',outfilename)
    #% We open the ODB defined at the beginning and create the replay file.
    try:
        o1 = session.openOdb(name=odbfullpath)
    except:
        continue
    else:
        odb = session.odbs[odbfullpath]
        #check if it is coarse, medium or fine
        #first we obtain all the strange variable names in history data
        #We retrieve them from beat 1 if it exists
        odbsteps=odb.steps.keys()
        if 'BEAT1' not in odbsteps:
            continue
        odbhistoryvars=odb.steps['BEAT1'].historyRegions.keys()

        coarse=0
        medium=0
        fine=0
        for odbhistoryvar in odbhistoryvars:
            # sys.__stderr__.write('Var: %s\n'%(odbhistoryvar))
            if 'R_ATRIUM-1' in odbhistoryvar:
                RAnodenum=odbhistoryvar.split('.')[-1]
                if RAnodenum in coarse_v[1]:
                    coarse=1
                if RAnodenum in medium_v[1]:
                    medium=1
                if RAnodenum in fine_v[1]:
                    fine=1
        #sys.__stderr__.write('Coarse: %i, Medium: %i, Fine: %i\n'%(coarse,medium,fine))
        # We use the property that Python considers 0 as False and >0 as True
        if coarse and (not medium) and (not fine):
            historyDataVarNames=coarse_v
        elif medium and (not coarse) and (not fine):
            historyDataVarNames=medium_v
        elif fine and (not medium) and (not coarse):
            historyDataVarNames=fine_v
        else:
            continue

        for i,outVarName in enumerate(outVarNames):
            session.XYDataFromHistory(name=outVarName, odb=odb, 
                outputVariableName=historyDataVarNames[i], 
                )
        
        listofxyDataObjects=[]
        for i,outVarName in enumerate(outVarNames):
            listofxyDataObjects.append(session.xyDataObjects[outVarName])
        
        session.xyReportOptions.setValues(interpolation=ON)
        session.writeXYReport(
            fileName=outfulladdress, appendMode=OFF,
            xyData=tuple(listofxyDataObjects))
        
        session.odbs[odbfullpath].close()
        
        #% Open again the file and give it a nice format.
        formatted_data=[]
        
        with open(outfulladdress,'r') as f:
            raw_data = f.readlines()
            
        for line in raw_data:
            if not not line.strip():
                templine=line.strip().split(' ')
                templineclean=[]
                for segment in templine:
                    if not not segment.strip(): #WTF does this mean???
                        templineclean.append(segment)
                formatted_data.append(','.join(templineclean)+'\n')
                
        f=open(outfulladdress,'w')
        f.writelines(formatted_data)
        f.close()