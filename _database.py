import os
import time

import constants as C

def Screate_metafile(name): #create metafile for series
    path = os.path.join(C.SF, name)
    
    chapters = next(os.walk(path))[1]


    #find last edited file
    times = set()
    for root, dirs, files in os.walk(path, topdown=False):
        for img in files:
            fp = os.path.join(root, img)    
            times.add( os.path.getmtime(fp) )
    last_edit = time.asctime(time.gmtime(max(times)))
            

    STRING = """NAME-:-{0} \nNUMBER_CHAPTERS-:-{1} \nLAST_EDITED-:-{2} \n""".format(name,len(chapters),last_edit)

    f_path = os.path.join(path, C.MetaF)
    f = open(f_path, 'w')    
    f.write( STRING )
    f.close()
    
    print ("CREATED META FILE FOR",name,"\n")
