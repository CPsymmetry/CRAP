import os, sys, datetime, tables, time, random, ROOT
import numpy as np
import pandas as pan
import shelve
from array import array
from glob import glob
from astral import LocationInfo
from astral.sun import sun

anomalous_param = 0 #Ammount of Data required for a particular hour to not be ignored as anomalous

gps_location = {
        '17001':{'gps':[51.5323159,-0.1204776], 'city':'London', 'region':'England', 'altitude':80.16},
        '14001':{'gps':[52.4498801,-1.9290455], 'city':'Birmingham', 'region':'England', 'altitude':204.14},
        '3001':{'gps':[52.1690478,4.4585983],'city':'Leiden', 'region':'Netherlands', 'altitude':52.38},
        '501':{'gps':[52.3558963,4.9509827],'city':'Amsterdam','region':'Netherlands', 'altitude':56.18},
        '601':{'gps':[52.6474195, 5.0691192],'city':'Werenfridus','region':'Netherlands','altitude':43.77},
        '15001':{'gps':[50.865468,-.0857862],'city':'Sussex','region':'England','altitude':128.7},
        }


def date_time(date):
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:])
    #proper refers to the formal date
    proper = datetime.datetime(year, month, day)
    
    return proper

def shelf_data(data, sh):
    filename = f'{sh[3]}/data_{sh[0]}_{sh[1]}_{sh[2]}.shlf'
    shelf = shelve.open(filename)
    
    shelf['data'] = data

    shelf.close()
    
    print(f'Data been shelved at filename:{filename}')


def day_time_cycles(date, station):

    proper = date
    if not isinstance(date, datetime.date):
        proper = date_time(date)
    
    location = gps_location[str(station)]

    city = LocationInfo(location['city'], location['region'], 'timezone/name', 
                        location['gps'][0], location['gps'][1])
    s = sun(city.observer, proper)
    
    daytime = [s['sunrise'].hour + 1, s['sunset'].hour]
    nighttime = [s['dusk'].hour + 1, s['dawn'].hour]
    return daytime, nighttime, location

def process_data_clump(events, date, station):
    #Processes one days worth of data
 
    timestamp = np.array(events.loc[:,'timestamp'])
    
    t0 = timestamp[0]
    n = 0
    dc = np.array([])
    ph = []
    data_clump = []

    #Extra Variables
    day_mean = 0
    night_mean = 0
    mean = []
    day_deviation = 0
    night_deviation = 0
    deviation = []
    dayph = []
    nightph = []
    sig_dif = False
    daytime, nighttime, location = day_time_cycles(date, station)

    for i in range(24):
        t1 = t0 + 3600*(i+1)
        dif = np.absolute(timestamp - t1)
        minindex = dif.argmin()
        sel_events = events.loc[n:minindex,:]
        n += len(sel_events)

        data_clump.append(sel_events)
        ph.append(sel_events['pulseheights'].to_numpy())
        dc = np.append(dc, sum(sel_events['pulseheights']))
        
   #Mean And Deviation
    dayph = dc[daytime[0]:]
    nightph = np.concatenate((dc[nighttime[0]:], dc[:nighttime[1]]))
        
    day_mean = sum(dayph)/len(dayph)
    night_mean = sum(nightph)/len(nightph)

    day_deviation = np.sqrt(sum((dayph - day_mean)**2)/len(dayph))
    night_deviation = np.sqrt(sum((nightph - night_mean)**2)/len(nightph))

    diff = abs(day_mean-night_mean)/np.sqrt(day_deviation**2 + night_deviation**2)
    n = 0
    for ls in ph:
        if len(ls) > anomalous_param:
            mean.append(sum(ls)/len(ls))
            deviation.append(np.sqrt(sum((ls - mean[n])**2)/len(ls)))
        else:
            mean.append(0)
            deviation.append(0)

        n += 1

    if diff > 3:
        sig_dif = True

    return {'events':{
                'data_clump':data_clump,
                'ph':ph,
                'day':dayph,
                'night':nightph,
                },
            'mean':{
                'day':day_mean,
                'night':night_mean,
                'ph':mean,
                },
            'deviation':{
                'ph':deviation,
                'day':day_deviation,
                'night':night_deviation,
                'diff':diff,
                'sig_dif':sig_dif,

                },
            'date':date,
            'station':station,
            'location':location,
            }

def data_chop(data):
    
    ph = np.sum(data['pulseheights'], axis = 1)
    sel = {'timestamp':data['timestamp'],'pulseheights':ph}
    df = pan.DataFrame(sel)
    
    return df

def seperate_data_clumps(events, date, station, d):

    start_proper = date_time(date[0])
    end_proper = date_time(date[1])
    
    delta_time = end_proper - start_proper

    timestamp = np.array(events.col('timestamp'))
    
    t0 = timestamp[0]
    n = 0
    pdc = []

    for i in range(delta_time.days):
        t1 = t0 + 86400*(i+1)
        dif = np.absolute(timestamp - t1)
        minindex = dif.argmin()
        tl = timestamp[minindex]
        sel_events = events.read_where('(timestamp < tl)')
        sel_events = sel_events[n:]
        n += len(sel_events)
        
        new_date = start_proper + datetime.timedelta(days=i)
        
        if len(sel_events) > 0:
            data_clump = data_chop(sel_events)
            pd = process_data_clump(data_clump, new_date, station)
            pdc.append(pd)

            d += 1
            m=f'{d}# days worth tabulated'
            sys.stdout.write('\r'+m)
            time.sleep(0.5)

    if len(pdc) == 1:
        pdc = pdc[0]

    return pdc, d

def analyse_data_clumps(files, shelf, shlfdir):
    pd = []
    start = 999999999999999
    end = 1
   
    d = 0

    for file in files:
        data = tables.open_file(file, 'r')
        keys = file.split('_')
        station = int(keys[1])
        start_date = int(keys[2])
        end_date = int(keys[3][:-3])
        
        events = data.root[f's{station}'].events
        
        if len(events) > 0:
            pdc, d = seperate_data_clumps(events, [str(start_date), str(end_date)], str(station), d)
            pd.append(pdc)
            
            if end_date>end:
                end = end_date

            if start_date<start:
                start = start_date

            if shelf == '--sd':
                sh = [station, start_date, end_date, shlfdir]
                shelf_data(pdc, sh)

    if len(pd) == 1:
        pd = pd[0]

    return pd

def parse_data(filedir, par = '--n', shelf = '--n', shlfdir = 'psd'):
    
    files = []
    if par == '--n':
        files = [filedir]
    elif par == '--all':
       files = glob(f'{filedir}/*.h5')

    elif par == '--any':        
        rnd = str(random.choice(os.listdir(filedir)))
        files = [f'{filedir}/{rnd}']
    
    pdc = analyse_data_clumps(files, shelf, shlfdir)

    return pdc

if __name__=="__main__":
    data = []
    filename = sys.argv[1]
    par = '--n'
    shelf = '--n'
    shlfdir = 'psd'
    ln = len(sys.argv)
    if ln > 2:
        par = sys.argv[2]
        if ln > 3:
            shelf = sys.argv[3]
            if ln == 5:
               shlfdir = sys.argv[4] 

    data = parse_data(filename, par, shelf, shlfdir)
