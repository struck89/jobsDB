# -*- coding: utf-8 -*-
#"""
#This file can only be run by Abaqus as a python script
# It can be run by running >'localabaq.bat cae nogui=exportPVresultsfromallODBs.py'
#"""

import visualization
import os

rootf='D:/users/eta2/hCxBvf'
#%% Get from an Abaqus replay file the weird names needed to access the
#   history output data. The names are stored in a list called 
#   llistOfStrangeVarNames

llistOfStrangeVarNames=[]
with open(rootf+'/abq_replayfile_PandV_variablenames.txt',
          'r') as f:
    raw_data = f.readlines()
    
for line in raw_data:
    if line[4:7]=='out':
        llistOfStrangeVarNames.append(line[24:-4])  

#%% Generate easy names. If the list of variables extracted above changes,
#   this piece of code below must change reflecting the modifications.
#   Using the base_string it generates a list of strings using pairs of it
#   Example:   ['FE',3] would generate ['FE1','FE2',FE3']
#   The name definitions at the end of the file

base_string=['P',7,'V',7]#,'MFO',7,'FE',3,'FV',3,'FT',3,'X',3,'dX',3,'ddX',3]
llistOfSimpleVarNames=[]

for i,acro in enumerate(base_string[::2]):
    repetitions=base_string[1::2][i]
    for num in range(repetitions):
        llistOfSimpleVarNames.append(acro+str(num+1))
#%%
# get ODBs in ODBs folder that are NOT in results folder:
folderRes=rootf+'/results'
results=os.listdir(folderRes)
results=[filename[:-4] for filename in results]
folderODBs=rootf+'/ODBs'
files=os.listdir(folderODBs)

odbs=[]
for odbwannabe in files:
    if (odbwannabe[-4:].lower()=='.odb') and \
       (odbwannabe[:-4]+'_PV' not in results):
        odbs.append(folderODBs+'/'+odbwannabe)
odbs.sort()
#%% Let's copy!!

for odbfullpath in odbs:
    odbname=odbfullpath.split('/')[-1]
    outfilename=odbname[:-4]+'_PV.csv'
    outfulladdress=rootf+'/results/'+outfilename    
    #% We open the ODB defined at the beginning and create the replay file.
    o1 = session.openOdb(name=odbfullpath)
    odb = session.odbs[odbfullpath]
    
    for i,simpleVarName in enumerate(llistOfSimpleVarNames):
        session.XYDataFromHistory(name=simpleVarName, odb=odb, 
            outputVariableName=llistOfStrangeVarNames[i], 
            )
    
    listofxyDataObjects=[]
    for i,simpleVarName in enumerate(llistOfSimpleVarNames):
        listofxyDataObjects.append(session.xyDataObjects[simpleVarName])
    
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

        
#%% Definitions
#        
#        P    Pressure
#        V    Volume
