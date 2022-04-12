import sapphire as sap
import tables, datetime, sys, math
from sapphire import esd
from glob import glob


station = sys.argv[1]
startDate = str(sys.argv[2])
endDate = str(sys.argv[3])
if len(startDate) != 8 or len(endDate) != 8:
    raise Exception("Invalid Date String")

startYear=int(startDate[:4])
startMonth=int(startDate[4:6])
startDay=int(startDate[6:])

endYear=int(endDate[:4])
endMonth=int(endDate[4:6])
endDay=int(endDate[6:])
    
sdate = datetime.datetime(year = startYear, month = startMonth, day = startDay)
edate = datetime.datetime(year = endYear, month = endMonth, day = endDay)
    

if len(sys.argv) == 4:

    data = tables.open_file(f'./data/data_{station}_{startDate}_{endDate}.h5','w')
    esd.download_data(data, f'/s{station}', int(station), sdate, edate)
    
elif len(sys.argv) == 5:
   
    timedelta = edate - sdate
    
    if sys.argv[4] == '--cycle' or sys.argv[4] == '--c':
        
        for i in range(timedelta.days):
            start = sdate + datetime.timedelta(days = i)
            end = start + datetime.timedelta(days = 1)
            
            prntsdate = f'{start.year}{start.month:02d}{start.day:02d}'
            prntedate = f'{end.year}{end.month:02d}{end.day:02d}'

            data = tables.open_file(f'./data/data_{station}_{prntsdate}_{prntedate}.h5','w')
            
            esd.download_data(data, f'/s{station}', int(station), start, end)

    elif sys.argv[4] == '--sw':
        
        ln = math.ceil(timedelta.days/365) - 1

        for i in range(ln):
            sstart = datetime.datetime(day = 1, month = 7, year = sdate.year+i)
            send = datetime.datetime(day=1, month = 8, year = sdate.year+i)
            
            wstart = datetime.datetime(day = 1, month = 1, year = sdate.year+i)
            wend = datetime.datetime(day=1,month=2,year=sdate.year+i)
            
            prntsdate = f'{sstart.year}{sstart.month:02d}{sstart.day:02d}'
            prntedate = f'{send.year}{send.month:02d}{send.day:02d}'

            data = tables.open_file(f'./data/summer_{station}_{prntsdate}_{prntedate}.h5','w')
            
            esd.download_data(data, f'/s{station}', int(station), sstart, send)

            wprntsdate = f'{wstart.year}{wstart.month:02d}{wstart.day:02d}'
            wprntedate = f'{wend.year}{wend.month:02d}{wend.day:02d}'

            wdata = tables.open_file(f'./data/winter_{station}_{wprntsdate}_{wprntedate}.h5','w')
            
            esd.download_data(wdata, f'/s{station}', int(station), wstart, wend)



#files=glob("data_*_*_*.h5")'

