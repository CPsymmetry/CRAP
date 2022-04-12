import os, sys, shelve, datetime, math, random, ROOT
from glob import glob
import numpy as np

###############CORE FUNCTIONS################

def tdate(date):
    return ROOT.TDatime(date.year,date.month,date.day,0,0,0)

def dts(date):
    return f'{date.year}/{date.month}/{date.day}'

def axis_to_date(mgr, hourly=False):
    mgr.GetXaxis().SetTimeDisplay(1)
    mgr.GetXaxis().SetNdivisions(503)
    if hourly:
        mgr.GetXaxis().SetTimeFormat("%Y-%m-%d %H:%m")
    else:
        mgr.GetXaxis().SetTimeFormat("%Y-%m-%d")
    
    mgr.GetXaxis().SetTimeOffset(0,"gmt")
    return mgr

def save_data(canvas, filename, filedir):
    return canvas.SaveAs(f'{filedir}/{filename}.pdf')

def parse_data(filedir, par = '--n'):
    file = []
    if par == '--n':
        file = [filedir]
    elif par == '--all':
        file = glob(f'{filedir}/*.shlf')
    elif par == '--any':
        rnd = str(random.choice(os.listdir(filedir)))
        file = [f'{filedir}/{rnd}']
    
    return file

def canvas_joiner(graphs):
    n = len(graphs)

    if n == 0:
        return None

    nx = math.sqrt(n)
    ny = math.floor(nx)
    
    if nx - ny != 0:
        nx = ny + 1

    jcanvas=ROOT.TCanvas('jcanvas', 'Cosmic Ray Analysis', 1000, 500)
    jcanvas.Divide(nx, ny)
    m = 1
    for gd in graphs:
        jcanvas.cd(m)
        ngd = gd
        ngd['canvas'] = jcanvas
        graph_maker(ngd)
        m += 1

    jcanvas.Update()
    
    return {'canvas':jcanvas}

def graph_maker(graph_data):
    graph = graph_data['graph']
    par = graph_data['par']
    
    if graph_data.get('canvas', None) == None:
        graph_data['canvas'] = ROOT.TCanvas('canvas','Cosmic Ray Analysis', 700, 500)

    graph.Draw(par)

    if graph_data.get('legend', None) != None:
        graph_data['legend'].Draw()
    
    return graph_data
  
###########MANIPULATION FUNCTIONS############# 

###############GRAPH FUNCTIONS################

def background_reducted_count(datafile):
    n = len(datafile)

    gr = ROOT.TGraph()
    m = -1
    for i in range(n):
        data = datafile[i]
        
        daymean = sum(data['mean']['ph'])/24

        for v in range(23):
            event_clump = data['events']['data_clump'][v]
            for events in event_clump:
                kn = len(events['pulseheight'])
                for k in range(kn-1):
                    m+=1
                    x = events['timestamp'][k]
                    y = events['pulseheight'][k] - daymean
                
                    gr.SetPoint(m,x,y)

        if n < 5:
            hourly = True

        gr.SetLineColor(2)
        gr.SetTitle(f'Reduced Mean Pulseheight Variations for the {datafile[0]["location"]["city"]} Detector')
        gr.GetYaxis().SetTitle('Reduced Particle Flux')
        gr.GetXaxis().SetTitle('Date Time')

        gr = axis_to_date(gr, hourly)
        
        return {'canvas':None,
                'graph':gr,
                'par':'alp',}

def pulse_daily_count(datafile):
    n = len(datafile)
    hourly = False

    gr = ROOT.TGraph()
    m = -1        
    for i in range(n):
        data = datafile[i]
        print(1) 
        for v in range(23):
            m += 1
            
            dtime = data['date'] + datetime.timedelta(hours=v)

            x = tdate(dtime).Convert()
            y = data['mean']['ph'][v]

            print(x,y)

            gr.SetPoint(m,x,y)

    if n < 5:
        hourly = True

    gr.SetLineColor(2)
        
    gr.SetTitle(f'Mean Pulseheight Variations for the {datafile[0]["location"]["city"]} Detector')
    gr.GetYaxis().SetTitle('# Of Particles Detected')
    gr.GetXaxis().SetTitle('Date Time')
    
    gr = axis_to_date(gr, hourly)
    
    return {'canvas':None,
            'graph':gr,
            'par':'alp'}
 
def pulse_mean_day_night_count(datafile):
    n = len(datafile)

    gr = ROOT.TGraph()
    gr1 = ROOT.TGraph()

    for i in range(n):
        data = datafile[i]

        x = tdate(data['date']).Convert()
        y = data['mean']['day']
        y1 = data['mean']['night']

        gr.SetPoint(i,x,y)
        gr1.SetPoint(i,x,y1)
        

    gr.SetLineColor(2)
    
    mgr = ROOT.TMultiGraph()

    mgr.Add(gr, "C")
    mgr.Add(gr1, "C")
    
    mgr.SetTitle(f'Day-Night Pulseheight Variations from the {datafile[0]["location"]["city"]} Detector')
    mgr.GetYaxis().SetTitle('# Of Particles Detected')
    mgr.GetXaxis().SetTitle('Date Time')
    
    mgr = axis_to_date(mgr)
    
    legend = ROOT.TLegend(.7,0.84,.95,.94)
    legend.SetHeader('The Legend', 'C')
    legend.AddEntry(gr,'Day variations of mean pulseheight', 'f')
    legend.AddEntry(gr1, 'Night variations of mean pulseheight', 'l')

    #canvas.SaveAs(filename+".pdf")
    return {'canvas':None,
            'graph':mgr,
            'par':'ap',
            'legend':legend
            }
   

def sig_dif(datafile):
    n = len(datafile)

    gr = ROOT.TGraph()

    for i in range(n):
        data = datafile[i]

        x = tdate(data['date']).Convert()
        y = data['deviation']['diff']

        gr.SetPoint(i,x,y)
    
    gr.SetTitle(f'Day-Night Pulseheight Deviation from the {datafile[0]["location"]["city"]} Detector')
    gr.GetYaxis().SetTitle('Deviation')
    gr.GetXaxis().SetTitle('Date Time')

    gr.SetMarkerSize(.5)
    gr.SetMarkerStyle(20)
    
    gr = axis_to_date(gr)

    return {'canvas':None,
            'graph':gr,
            'par':'AP'}
def summer_winter_day(datafile):
    n = len(datafile)
     
    summer_month = 7
    winter_month = 1
    grs = ROOT.TGraph()
    grw = ROOT.TGraph()

    summer = {}
    winter = {}

    for i in range(n):
        data = datafile[i]
        month = data['date'].month
        if month == summer_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = summer.keys()
            
            deviation = np.array(data['deviation']['day'])
            mean = data['mean']['day']

            if year in keys:
                summer[year]['data'].append(data)
                summer[year]['mean'].append(mean)
                np.append(summer[year]['deviation'],deviation)
            else:
                summer[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

        elif month == winter_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = winter.keys()
            deviation = np.array(data['deviation']['day'])
            mean = data['mean']['day']

            if year in keys:
                winter[year]['data'].append(data)
                winter[year]['mean'].append(mean)
                np.append(winter[year]['deviation'],deviation)
            else:
                winter[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }
    s = -1
    w = -1
    for year in winter:
        for i in winter[year]['mean']:
            w += 1
            grw.SetPoint(w,w,i)
        for i in summer[year]['mean']:
            s += 1
            grs.SetPoint(s,s,i)
   
    grs.SetLineColor(2)
    
    mgr = ROOT.TMultiGraph()
    
    mgr.Add(grs, "C")
    mgr.Add(grw, "C")
    
    mgr.SetTitle(f'Summer-Winter Pulseheight Variations Using Day Data from the {datafile[0]["location"]["city"]} Detector')
    mgr.GetYaxis().SetTitle('# Of Particles Detected')
    mgr.GetXaxis().SetTitle('Days')
    
    legend = ROOT.TLegend(.7,0.84,.95,.94)
    legend.SetHeader('The Legend', 'C')
    legend.AddEntry(grs,'July  variations of mean pulseheight', 'f')
    legend.AddEntry(grw, 'January variations of mean pulseheight', 'l')

    #canvas.SaveAs(filename+".pdf")
    return {'canvas':None,
            'graph':mgr,
            'par':'ap',
            'legend':legend
            }
   

def summer_winter_variations_day(datafile):
    n = len(datafile)
     
    summer_month = 7
    winter_month = 1
    gr = ROOT.TGraph()

    summer = {}
    winter = {}

    for i in range(n):
        data = datafile[i]
        month = data['date'].month
        if month == summer_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = summer.keys()
            
            deviation = np.array(data['deviation']['day'])
            mean = data['mean']['day']

            if year in keys:
                summer[year]['mean'].append(mean)
                np.append(summer[year]['deviation'],deviation)
                summer[year]['data'].append(data)
            else:
                summer[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

        elif month == winter_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = winter.keys()
            deviation = np.array(data['deviation']['day'])
            mean = data['mean']['day']

            if year in keys:
                winter[year]['mean'].append(mean)
                np.append(winter[year]['deviation'],deviation)
                winter[year]['data'].append(data)
            else:
                winter[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

    for year in winter:
        wdata = winter[year]
        winter[year]['mean'] = sum(wdata['mean'])/len(wdata['mean'])
        winter[year]['deviation'] = np.sqrt(sum(wdata['deviation'])**2)/len(wdata['deviation'])
    for year in summer:
        sdata = summer[year]
        summer[year]['mean'] = sum(sdata['mean'])/len(sdata['mean'])
        summer[year]['deviation'] = np.sqrt(sum(sdata['deviation']**2))/len(sdata['deviation'])
        
    l = 0
    for year in winter:
        sdata = summer[year]
        wdata = winter[year]
        smean = sdata['mean']
        sdif = sdata['deviation']
        wmean = wdata['mean']
        wdif = wdata['deviation']
        diff = abs(smean-wmean)/np.sqrt(sdif**2 + wdif**2)
        year = year.split('.')[1]
        gr.SetPoint(l,int(year),diff)
        l += 1

    gr.SetTitle(f'Summer-Winter Pulseheight Deviations. Data from the {datafile[0]["location"]["city"]} Detector')
    gr.GetYaxis().SetTitle('Deviation')
    gr.GetXaxis().SetTitle('Years')
    
    gr.SetMarkerSize(.5)
    gr.SetMarkerStyle(20)

    return {'canvas':None,
            'graph':gr,
            'par':'AP'}

def pulseheight_count(datafile):
    
    h1 = ROOT.TH1F('count','count',100,0,3000)
    
    for data in datafile:
        ph = data['events']['ph']
        for hours in ph:
            for pulseheight in hours:
                h1.Fill(pulseheight)
    
    start_date = dts(datafile[0]['date'])
    end_date = dts(datafile[-1]['date']+datetime.timedelta(days=1))
    h1.SetTitle(f'Pulseheight count from the {datafile[0]["location"]["city"]} Detector from {start_date} to {end_date}')
    h1.GetYaxis().SetTitle('Pulse Count')
    h1.GetXaxis().SetTitle('Pulse Intensity')

    return {'canvas':None,
            'graph':h1,
            'par':''}


def summer_winter(datafile):
    n = len(datafile)
     
    summer_month = 7
    winter_month = 1
    grs = ROOT.TGraph()
    grw = ROOT.TGraph()

    summer = {}
    winter = {}

    for i in range(n):
        data = datafile[i]
        month = data['date'].month
        if month == summer_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = summer.keys()
            
            dev = np.array(data['deviation']['ph'])
            mean = sum(data['mean']['ph'])/24
            deviation = np.sqrt(sum(dev**2))/24

            if year in keys:
                summer[year]['mean'].append(mean)
                np.append(summer[year]['deviation'],deviation)
                summer[year]['data'].append(data)
            else:
                summer[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

        elif month == winter_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = winter.keys()
            dev = np.array(data['deviation']['ph'])
            mean = sum(data['mean']['ph'])/24
            deviation = np.sqrt(sum(dev**2))/24

            if year in keys:
                winter[year]['mean'].append(mean)
                np.append(winter[year]['deviation'],deviation)
                winter[year]['data'].append(data)
            else:
                winter[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

    s = -1
    w = -1
    for year in winter:
        for i in winter[year]['mean']:
            w += 1
            grw.SetPoint(w,w,i)
        for i in summer[year]['mean']:
            s += 1
            grs.SetPoint(s,s,i)
   
    grs.SetLineColor(2)
    
    mgr = ROOT.TMultiGraph()
    
    mgr.Add(grs, "C")
    mgr.Add(grw, "C")
    
    mgr.SetTitle(f'Summer-Winter Pulseheight Variations Using Day Data from the {datafile[0]["location"]["city"]} Detector')
    mgr.GetYaxis().SetTitle('# Of Particles Detected')
    mgr.GetXaxis().SetTitle('Days')
    
    legend = ROOT.TLegend(.7,0.84,.95,.94)
    legend.SetHeader('The Legend', 'C')
    legend.AddEntry(grs,'July  variations of mean pulseheight', 'f')
    legend.AddEntry(grw, 'January variations of mean pulseheight', 'l')

    #canvas.SaveAs(filename+".pdf")
    return {'canvas':None,
            'graph':mgr,
            'par':'ap',
            'legend':legend
            }
   


def summer_winter_variations(datafile):
    n = len(datafile)
     
    summer_month = 7
    winter_month = 1
    gr = ROOT.TGraph()

    summer = {}
    winter = {}

    for i in range(n):
        data = datafile[i]
        month = data['date'].month
        if month == summer_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = summer.keys()
            
            dev = np.array(data['deviation']['ph'])
            mean = sum(data['mean']['ph'])/24
            deviation = np.sqrt(sum(dev**2))/24

            if year in keys:
                summer[year]['mean'].append(mean)
                np.append(summer[year]['deviation'],deviation)
                summer[year]['data'].append(data)
            else:
                summer[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

        elif month == winter_month:
            year = data['date'].year
            year = f'year.{year}'
            keys = winter.keys()
            dev = np.array(data['deviation']['ph'])
            mean = sum(data['mean']['ph'])/24
            deviation = np.sqrt(sum(dev**2))/24

            if year in keys:
                winter[year]['mean'].append(mean)
                np.append(winter[year]['deviation'],deviation)
                winter[year]['data'].append(data)
            else:
                winter[year] = {'data':[data],
                                'mean':[mean],
                                'deviation':np.array([deviation]),
                                }

    for year in winter:
        wdata = winter[year]
        winter[year]['n'] = len(wdata['mean'])*24
        winter[year]['mean'] = sum(wdata['mean'])/len(wdata['mean'])
        winter[year]['deviation'] = np.sqrt(sum(wdata['deviation'])**2)/len(wdata['deviation'])
    for year in summer:
        sdata = summer[year]
        summer[year]['n'] = np.sqrt(len(sdata['mean'])*24)
        summer[year]['mean'] = sum(sdata['mean'])/len(sdata['mean'])
        summer[year]['deviation'] = np.sqrt(sum(sdata['deviation']**2))/len(sdata['deviation'])
        
    l = 0
    for year in winter:
        sdata = summer[year]
        wdata = winter[year]
        smean = sdata['mean']
        sdif = sdata['deviation']
        wmean = wdata['mean']
        wdif = wdata['deviation']
        diff = abs(smean-wmean)/np.sqrt(sdif**2 + wdif**2)
        year = year.split('.')[1]
        gr.SetPoint(l,int(year),diff)
        l += 1

    gr.SetTitle(f'Summer-Winter Pulseheight Deviations. Data from the {datafile[0]["location"]["city"]} Detector')
    gr.GetYaxis().SetTitle('Deviation')
    gr.GetXaxis().SetTitle('Years')
    
    gr.SetMarkerSize(.5)
    gr.SetMarkerStyle(20)

    return {'canvas':None,
            'graph':gr,
            'par':'AP'}

def pulseheight_count(datafile):
    
    h1 = ROOT.TH1F('count','count',100,0,3000)
    
    for data in datafile:
        ph = data['events']['ph']
        for hours in ph:
            for pulseheight in hours:
                h1.Fill(pulseheight)
    
    start_date = dts(datafile[0]['date'])
    end_date = dts(datafile[-1]['date']+datetime.timedelta(days=1))
    h1.SetTitle(f'Pulseheight count from the {datafile[0]["location"]["city"]} Detector from {start_date} to {end_date}')
    h1.GetYaxis().SetTitle('Pulse Count')
    h1.GetXaxis().SetTitle('Pulse Intensity')

    return {'canvas':None,
            'graph':h1,
            'par':''}


###############MAIN PROGRAM################



graph_functions = {
        '--pm':pulse_mean_day_night_count,
        '--pd':pulse_daily_count,
        '--pc':pulseheight_count,
        '--sd':sig_dif,
        '--brc':background_reducted_count,
        '--sw':summer_winter,
        '--swv':summer_winter_variations,
        '--swd':summer_winter_day,
        '--swvd':summer_winter_variations_day,
        }

functions = {
        '--append':canvas_joiner,
        'save-data':save_data,
        }

manipulations = {


        }

filedir = sys.argv[1]
par = '--n'

if len(sys.argv) > 2:
    par = sys.argv[2]
    
files = []
file = {'data':[]}
filedir = parse_data(filedir, par)

if len(filedir) == 1:
    file = shelve.open(filedir)
    files.append(file)
elif len(filedir) > 1:
    for f in filedir:
        fl = shelve.open(f)
        files.append(fl)
        for i in fl['data']:
            file['data'].append(i)
elif len(filedir) == 0:
    raise Exception('ERROR: file required to run')

datafile = file['data']

graph_keys = graph_functions.keys()
function_keys = functions.keys()
manipulation_keys = manipulations.keys()

if not isinstance(datafile, list):
    datafile = [datafile]

data_keys = datafile[0].keys()
        

default_graph_dir = './graphs'
unidentified_graphs = 0

cont = True
while cont:
    var = input('Enter Manipulation...')

    if var == 'quit' or var == 'q':
        cont = False
        exit

    inp = var.split(' ')

    if inp[0] in graph_keys:
        graph_data  = graph_functions[inp[0]](datafile)
        graph_data = graph_maker(graph_data)
        graph_data['canvas'].Update()
        
        #Processing Secondary Input#
        ninp = input('Graph Displayed ...')
        
        sinp = ninp.split(' ')
    
        if ninp == 'quit' or ninp == 'q':
            cont = False
            exit
        elif sinp[0] == 'save-data':
            if len(sinp) < 2:
                sinp.append(default_graph_dir)
            if len(sinp) < 3:
                sinp.append(f'Graph{unidentified_graphs}')
                unidentified_graphs += 1
            functions[sinp[0]](graph_data['canvas'],sinp[2], sinp[1]) #F
        #End#
    elif inp[0] in function_keys:
        if inp[0] == '--append':
            graphs = []
            for gfn in inp:
                if gfn in graph_keys:
                    gd = graph_functions[gfn](datafile) 
                    graphs.append(gd)
            graph_data = functions[inp[0]](graphs)
        ninp = input('Graphs Displayed ...')

        #Processing Seconary Input#
        sinp = ninp.split(' ')
    
        if ninp == 'quit' or ninp == 'q':
            cont = False
            exit
        elif sinp[0] == 'save-data':
            if len(sinp) < 2:
                sinp.append(f'Graph{unidentified_graphs}')
                unidentified_graphs += 1

            if len(sinp) < 3:
                sinp.append(default_graph_dir)
             
            functions[sinp[0]](graph_data['canvas'],sinp[1], sinp[2]) #F
        #End#
    elif inp[0] in manipulation_keys:
        print('...')
    elif cont:
        print('invalid Manipulation,')

for file in files:
    file.close()

