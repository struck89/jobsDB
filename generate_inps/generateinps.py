# -*- coding: utf-8 -*-
"""
Created on Mon Oct  3 00:04:47 2016

@author: Enric
"""
import shutil
import os

def generate_inp(num_beats=3,sufix='mod',mod_values_file='mod_values.txt'):
    # read the parameters to generate the inp. The default ones
    with open('base_values.txt','r') as f:
        base_values=f.readlines()
    param_dict={l.split(':')[0]:l.split(':')[1].strip() for l in base_values}
    # read the desired modifications and record them in the parameters dictionary
    with open(mod_values_file,'r') as f:
        mod_values=f.readlines()
    mod_dict={l.split(':')[0]:l.split(':')[1].strip() for l in mod_values}
    for param,value in mod_dict.items():
        if value[0].lower()=='x':
            param_dict[param]=str(float(param_dict[param])*float(value[1:]))
        elif value[0].lower()=='/':
            param_dict[param]=str(float(param_dict[param])/float(value[1:]))
        else:
            param_dict[param]=value
    # intro
    rootf=os.getcwd()
    src='part01'
    src=os.path.join(rootf,src)
    dst='hC%iBvf_%s.inp'%(num_beats,sufix)
    dst=os.path.join(rootf,dst)
    shutil.copyfile(src,dst)
    # parts to personalize
    perso_part=""
    with open('part02_compliances','r') as f:
        perso_part+=f.read()
    with open('part03','r') as f:
        perso_part+=f.read()
    with open('part04_preloadtime','r') as f:
        perso_part+=f.read()
    with open('part05','r') as f:
        perso_part+=f.read()
    with open('part06_resistances','r') as f:
        perso_part+=f.read()
    with open('part07','r') as f:
        perso_part+=f.read()
    with open('part08_valveareas','r') as f:
        perso_part+=f.read()
    with open('part09_preloadpressures','r') as f:
        perso_part+=f.read()
    with open('part10_endpreload','r') as f:
        perso_part+=f.read()
    for param,value in param_dict.items():
        perso_part=perso_part.replace(param,value)
    if perso_part.count('@')!=0:
        print('Some parameter has not been replaced')
    with open(dst,'a') as g:
        g.write(perso_part)
    # beat1
    with open('part11_beat01','r') as f:
        beat1=f.read()
    with open('part12_recovery01','r') as f:
        beat1+=f.read()
    # rest of the beats
    with open('part13_beatX','r') as f:
        beatx=f.read()
    beats=beat1
    for beat_num in range(2,num_beats+1):
        beats+=beatx.replace('@BEAT_NUM','%i'%beat_num)
    with open(dst,'a') as g:
        g.write(beats)

def generate_various_inps(configfiles_file='experiments.txt',num_beats=3,sufix='mod'):
    with open(configfiles_file,'r') as f:
        config_files=f.readlines()
    for num,config_file in enumerate(config_files,start=1):
        generate_inp(num_beats=num_beats,sufix=sufix+'%02i'%num,\
                     mod_values_file=config_file.strip())