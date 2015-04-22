import os

import _database

import constants as C

 
done = False


series_l = sorted(next(os.walk(C.SF))[1]) #list of folders in the "Series" folder

print (len(series_l),"found")

library = {}
for ser in series_l: 
    path = os.path.join(C.SF,ser)
    con = os.listdir(path)
    library[ser] = {}
    if not C.MetaF in con: #if folder doesn't contain metadata file
        print ("\n","METAFILE NOT FOUND FOR",ser,"\n")
        database.Screate_metafile(ser)
    
    f_path = os.path.join(path, C.MetaF)
    f = open(f_path, 'r')    
    for line in f:
        key, value = line.split("-:-")
        library[ser][key] = value
    f.close()
   
print ("Your library contains these pieces")
for series in library:
    print ("Data for",series)
    for key in library[series]:
        print (key,":",library[series][key],)


#clean up for debug purposes
for ser in series_l: 
    path = os.path.join(C.SF, ser)
    f_path = os.path.join(path, C.MetaF)
    os.remove(f_path)    
    
    
