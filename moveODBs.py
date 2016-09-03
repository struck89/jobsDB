# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 15:58:49 2016

@author: eta2
"""

import os

def moveODBs():
    rootf='D:/users/eta2/hCxBvf'
    contents=os.listdir(rootf)
    folders=[]
    for thing in contents:
        if os.path.isdir(rootf+'/'+thing):
            folders.append(rootf+'/'+thing)
    ODBs=[]
    for folder in folders:
        contents=os.listdir(folder)
        for thing in contents:
            if thing[-3:].lower()=='odb':
                ODBs.append(folder+'/'+thing)
#    return ODBs
    for ODB in ODBs:
        src=ODB
        dst=src.split('/')
        dst=dst[:4]+['ODBs']+[dst[-1]]
        os.rename(src,'/'.join(dst))

#def removeelecodbs(listofodbs):
#    for odb in listofodbs:
#        if 'heart-elec-coarse.odb' in odb:
#            os.remove(odb)
