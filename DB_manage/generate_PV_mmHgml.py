# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 10:33:50 2016

@author: eta2
"""

import os
import pandas as pd

def gen_mmHgml(rootf='D:/users/eta2/hCxBvf'):
    res_files_MPa=os.listdir(rootf+'/results')
    res_files_MPa=[name[:-7] for name in res_files_MPa if name[-7:]=='_PV.csv']
    
    res_files_mmHg=os.listdir(rootf+'/results_mmHgml')
    res_files_mmHg=[name[:-11] for name in res_files_mmHg if name[-11:]=='_mmHgml.csv']
    
    files_to_process=[name for name in res_files_MPa if name not in res_files_mmHg]
    
    for jname in files_to_process:
        full_addr_in=os.path.join(rootf,'results',jname+'_PV.csv')
        full_addr_out=os.path.join(rootf,'results_mmHgml',jname+'_mmHgml.csv')
        
        df=pd.read_csv(full_addr_in)
        df.loc[:,'P1':'P7']=df.loc[:,'P1':'P7'].values*7500
        df.loc[:,'V1':'V7']=df.loc[:,'V1':'V7'].values*0.001
    
        df.to_csv(path_or_buf=full_addr_out,float_format="%.6g",index=False)
        
if __name__ == "__main__":
    gen_mmHgml()