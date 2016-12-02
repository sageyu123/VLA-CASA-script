import os
#### SCRIPT for calibrating the 20120310 data at L Band ####
mspath='/srg/bchen/EVLA/20120310/'
rawms_path='/srg/data/evla/20120310/'
calfile='cal_20120310A.1s.ms'
calfile_hs='cal_20120310A.hs.1s.ms'
calprefix='caltables/calSUN_20120310A'
slfcalprefix='caltables/calSUN_164252.slfcal'
msfile='sun_20120310A.50ms.ms'
msfile_1s='sun_20120310A.1s.ms'

#change directory to mspath
os.chdir(mspath)

info=0
flag=0
cal=0

#calibration controls
calsun=0

if info:
###### MS information  ######
#### listobs ####
    listobs(vis=rawms_path+msfile,listfile=mspath+msfile+'.listobs',overwrite=True)
#### plotants ####
    figfile=calfile+'.ants.png'
    plotants(vis=calfile)

if flag:
############################
##### Data Flagging #####
############################
#### flagcmd: apply telescope flags ####
    flagcmd(vis=calfile,inpmode='list',inpfile='onlineflgs_20120310A.flgcmd')

#### flagdata ####
    flagdata(vis=calfile, scan='0~6, 8, 10, 35, 37, 62, 64')
    flagdata(vis=calfile, mode='quack', quackmode='beg', quackinterval=6.0)
    #flagcmd(vis=msfile,inpmode='list',inpfile='manualflgs_20120310A.flgcmd')

#### problematic data ####
# ea05 all spws, cor LL has low amplitudes

if cal:
#############################
##### Calibrations ######
#############################
    gencal(vis=calfile,caltable=calprefix+'.antpos',caltype='antpos')
#### no need for correcting antenna position, caltable not created ####
#### gain curve calibration ####
    #gencal(vis=msfile,caltable=calprefix+'.gaincurve',caltype='gc')
        # All solutions are unity, NOT going to use it
#### setting flux density scale ####
    setjy(vis=msfile,field='3C48',model='3C48_L.im')


#### Reference Antenna ####
    refant='ea07'
    antennas='ea05,ea07,ea08,ea11,ea12,ea14,ea17,ea19,ea21,ea22,ea23,ea24,ea25,ea27,ea28'
    # cleanwindows for init phase solution
    goodspw0='0:60~65, 1:35~40, 2:60~65, 3:60~65, 4:41~46, 5~7:60~65'
    goodspw='0:2~17;19~46;51~53;58~62,1:2~25;30~40;44~50;56~62,2:2~8;13~21;24~62,\
             3:2~62,4:2~10;50~61,5:4~62,6~7:2~62'

#### initial phase-only solution ####
#clean spectral channels for all spws: 28~32
    gaincal(vis=calfile, caltable=calprefix+'.pha0', field='3C48', spw=goodspw0, gaintype='G', \
            gaintable=[calprefix+'.rq'],refant=refant, calmode='p', solint='10s', minsnr=3)

#### delay calibration ####
    badspw = [0, 1, 2, 3, 4, 5, 6, 7]
    badchannel = [\ # spw0
	[30, 89, 90, 91, 102], \ #spw1
	[117, 118],\
	[54, 74, 81, 82],\
	[],\
	[13,14,22]+range(26,30)+[36,38]+range(54,58)+range(97,112),\
	[38, 42, 43],\
	[],\
	[28, 38, 80]\
	]

    def get_goodspw(badspw, badchannel):
       goodspw = []
       for s, chan in zip(badspw, badchannel):
           if len(chan) != 0:
               spwstr = ['{}:{}~{}'.format(s, 3, chan[0])]
               for ll, item in enumerate(chan):
                   if ll < len(chan) - 1 and item + 1 != chan[ll + 1]:
                       spwstr.append('{}~{}'.format(item + 1, chan[ll + 1]))
               spwstr.append('{}~{}'.format(chan[-1] + 1, 124))
               goodspw.append('{}'.format(';'.join(spwstr)))
           else:
               goodspw.append('{}'.format(s))
       goodspw = ','.join(goodspw)
       return goodspw

    goodspw=get_goodspw(badspw, badchannel)
    goodspwdelay='0:3~29;31~88;92~102;103~124,\
               1:3~94;106~117;119~124,\
               2:3~54;55~74;75~81;83~124,\
               3:3~124,\
               4:3~12;16~21;23~25;30~54;59~80;82~97;112~124,\
               5:3~38;39~42;44~124,\
               6:3~124,\
               7:3~34;40~79;82~124'
    gaincal(vis=calfile, caltable=calprefix+'.delay', field='3C48', 
            spw=goodspwdelay, \
            gaintype='K', gaintable=[calprefix+'.rq', calprefix+'.pha0'],\
            gainfield=['','3C48'],refant=refant, \
            combine='scan',solint='inf', minsnr=3)

#### bandpass calibration ####
    goodspwbp='0:0~29;31~88;92~102;103~127,\
               1:0~94;106~117;119~127,\
               2:0~54;55~74;75~81;83~127,\
               3,\
               4:0~12;16~19;24~25;30~49;60~80;82~97;112~127,\
               5:0~38;39~42;44~127,\
               6,\
               7:0~34;40~79;83~127'
    # better to smooth only spw 4 and combine the smoothed spw 4 with all other (unsmoothed) spws
    hanningsmooth(vis=calfile,datacolumn='data',field='3C48',outputvis=calfile_hs)
    bandpass(vis=calfile_hs,caltable=calprefix+'.bp',field='3C48',spw=goodspwbp,\
             bandtype='B', refant=refant, fillgaps=20,\
             gaintable=[calprefix+'.rq',calprefix+'.pha0',calprefix+'.delay'],\
             gainfield=['','',''],\
             solnorm=False,combine='scan',solint='inf')
    # wrong delays on ea25, spw4, pol LL

#### gain calibration ####
## good spectral channels ##
## phase only solution PER SCAN (to be used on calibrate solar scans) ##
    gaincal(vis=msfile,caltable=calprefix+'.pha_inf',field='3C48',spw=goodspw,gaintype='G',\
            calmode='p',refant=refant,solint='inf',solnorm=False,\
            gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp'],\
            gainfield=['','',''])
    gaincal(vis=msfile,caltable=calprefix+'.pha_inf',field='J2130+0502',spw=goodspw,gaintype='G',\
            calmode='p',refant=refant,solint='inf',solnorm=False,\
            gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp'],\
            gainfield=['','',''],append=True)

## amp only solution PER SCAN ##
    gaincal(vis=msfile,caltable=calprefix+'.amp_inf',field='3C48',spw=goodspw,gaintype='G',\
            calmode='a',refant=refant,solint='inf',solnorm=False,\
            gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',calprefix+'.pha_inf'],\
            gainfield=['','','','3C48'],interp=['','nearest','nearest','nearest'])
    gaincal(vis=msfile,caltable=calprefix+'.amp_inf',field='J2130+0502',spw=goodspw,gaintype='G',\
            calmode='a',refant=refant,solint='inf',solnorm=False,\
            gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',calprefix+'.pha_inf'],\
            gainfield=['','','','J2130+0502'],interp=['','nearest','nearest','nearest'],append=True)

## amp only solution COMBING SCANs by applying the per int phase solutions (in order to bootstrap the flux for J1150-0023 ##
    gaincal(vis=msfile,caltable=calprefix+'.amp_comb',field='0',spw=goodspw,gaintype='G',\
            calmode='a',refant=refant,solint='inf',solnorm=False,combine='scan',\
            gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',calprefix+'.pha_inf'],\
            gainfield=['','1','1','0'],interp=['','nearest','nearest','nearest'])
    gaincal(vis=msfile,caltable=calprefix+'.amp_comb',field='1',spw=goodspw,gaintype='G',\
            calmode='a',refant=refant,solint='inf',solnorm=False,combine='scan',\
            gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',calprefix+'.pha_inf'],\
            gainfield=['','1','1','1'],interp=['','nearest','nearest','nearest'],append=True)

## scale the flux for J1150-0023 using fluxscale ##
    myflux=fluxscale(vis=msfile,caltable=calprefix+'.amp_comb',fluxtable=calprefix+'.amp_Finc',\
                     reference='1',transfer='0',incremental=True,listfile=calprefix+'.fscale_out')

#################################################
##### Apply calibrations to the calibrators #####
#################################################
#### 3C286 ####
    applycal(vis=msfile,field='1',gaintable=[calprefix+'.rq',calprefix+'.delay',\
             calprefix+'.bp',calprefix+'.pha_inf',calprefix+'.amp_inf'],\
             gainfield=['','1','1','1','1'],\
             interp=['','','','nearest','nearest'],parang=False,flagbackup=True)
#### J1347+1217 ####
    applycal(vis=msfile,field='0',gaintable=[calprefix+'.rq',calprefix+'.delay',\
             calprefix+'.bp',calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
             gainfield=['','1','1','0','0','0'],\
             interp=['','','','nearest','nearest','nearest'],parang=False,flagbackup=True)
#### More bad data found after applycal ####
### baseline ea01&ea13, ea05&ea13, ea09&ea13 @ spw5 and LL, both 3C286 and J1347+1217, probably bad for solar scans too? ##
    flagdata(vis=msfile,field='0,1',spw='5',antenna='ea01&ea13;ea05&ea13;ea09&ea13',correlation='LL')
    antennas='ea01,ea02,ea03,ea04,ea05,\
              ea06,ea07,ea08,ea09,ea10,\
              ea11,ea12,ea13,ea14,ea15,\
              ea16,ea17,ea19,ea20,ea21,\
              ea22,ea23,ea24,ea25,ea26,\
              ea27,ea28'
    par_mbd=[-0.020, -0.007, 0.111, 0.233, -0.018, -0.004, 0.005, 0.012, 0.087, 0.079, \
                0.005, 0.165, -0.001, -0.002, 0.003, 0.145, -0.004, 0.004, 0.023, -0.015, \
                -0.020, -0.013, 0.217, 0.225, 0.003, 0.003, -0.006, -0.006, -0.014, -0.015, \
                -0.007, 0.000, 0.007, 0.016, 0.098, 0.111, -0.004, 0.075, -0.007, 0.006, \
                -0.003, 0.010, -0.003, 0.005, -0.005, 0.010, -0.030, -0.024, -0.025, -0.011, \
                0.100, 0.109, -0.030, -0.015]
    par_pha=[0.0, -0.3, -0.8, -1.3, -1.9, -2.1, -2.6, -2.7, -1.5, 54.0,\
             -3.7, -3.5, 0.3, 0.7, -0.8, -0.8, -3.5, -3.7, -2.4, -2.6,\
             -2.1, -2.1, -3.3, -3.0, -1.3, -2.3, -1.6, -1.7, -3.6, -2.6, \
             1.4, 0.8, -0.1, 0.0, -1.5, -2.0, -3.3, -3.6, -1.4, -0.9,\
             -2.9, -2.4, 0.7, 0.2, -3.7, -4.4, -0.7, -0.6, -5.1, -6.0,\
             -4.7, -4.5, -1.8, -2.1]
    gencal(vis=msfile,caltable=calprefix+'.20db_mbd',caltype='mbd',spw='',\
           antenna=antennas,pol='R,L',parameter=par_mbd) 
    gencal(vis=msfile,caltable=calprefix+'.20db_pha',caltype='ph',spw='',\
           antenna=antennas,pol='R,L',parameter=par_pha) 

if calsun:
#### SUN ####
    if cal_ms_o1:
        msfile_sun01='SUN01_20141101.4s.16M.ms'
        applycal(vis=msfile_sun01,field='SUN01',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc',\
                 calprefix+'.20db_mbd',calprefix+'.20db_pha'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217','',''],\
                 interp=['','','','linear','linear','linear','',''],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_sun01, outputvis='SUN01_20141101.4s.16M.cal.ms',datacolumn='corrected')

    if cal_ms_o23:
        msfile_sun02='SUN02_20141101.4s.16M.ms'
        applycal(vis=msfile_sun02,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc',\
                 calprefix+'.20db_mbd',calprefix+'.20db_pha'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217','',''],\
                 interp=['','','','linear','linear','linear','',''],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_sun02, outputvis='SUN02_20141101.4s.16M.cal.ms',datacolumn='corrected')

    if cal_ms_o2_tp3:
        msfile_tp3='sun_20141101_t191020-191040.50ms.ms'
        flagdata(vis=msfile_tp3,antenna='ea12,ea16')
        applycal(vis=msfile_tp3,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_tp3, outputvis='sun_20141101_t191020-191040.50ms.cal.ms',datacolumn='corrected')

    if cal_ms_o2_c2flare:
        msfile_c2flare='sun_20141101_t181500-183000.50ms.ms'
        flagdata(vis=msfile_c2flare,antenna='ea12,ea16')
        applycal(vis=msfile_c2flare,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_c2flare, outputvis='sun_20141101_t181500-183000.50ms.cal.ms',datacolumn='corrected')

    if cal_ms_o3_1m:
        msfile_orb3_1min='sun_20141101_t201500-201600.50ms.ms'
        flagdata(vis=msfile_orb3_1min,antenna='ea12,ea16')
        applycal(vis=msfile_orb3_1min,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_orb3_1min, outputvis='sun_20141101_t201500-201600.50ms.cal.ms',datacolumn='corrected')

    if cal_ms_o3_5m:
        msfile_orb3_5min='sun_20141101_t201000-201500.50ms.ms'
        flagdata(vis=msfile_orb3_5min,antenna='ea12,ea16')
        applycal(vis=msfile_orb3_5min,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_orb3_5min, outputvis='sun_20141101_t201000-201500.50ms.cal.ms',datacolumn='corrected')

    if cal_ms_o3_40m:
        msfile_orb3_40m='sun_20141101_t1915-1955.1s.ms'
        flagdata(vis=msfile_orb3_40m,antenna='ea12,ea16')
        applycal(vis=msfile_orb3_40m,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_orb3_40m, outputvis='sun_20141101_t1915-1955.1s.cal.ms',datacolumn='corrected')

    if cal_ms_sun01:
        flagdata(vis=msfile_sun01,antenna='ea12,ea16')
        applycal(vis=msfile_sun01,field='SUN01',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_sun01, outputvis='sun01_20141101.50ms.cal.ms',\
              field='SUN01',datacolumn='corrected')
    if cal_ms_sun02:
        flagdata(vis=msfile_sun02,antenna='ea12,ea16')
        applycal(vis=msfile_sun02,field='SUN02',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc'],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217'],\
                 interp=['','','','linear','linear','linear'],\
                 spwmap=[],applymode='',parang=False,flagbackup=True)
        split(vis=msfile_sun02, outputvis='sun02_20141101.50ms.cal.ms',\
              field='SUN02',datacolumn='corrected')
    if cal_ms_c7:
        split(vis=msfile_sun01,outputvis=msfile_c7,timerange='16:35:00~17:00:00',datacolumn='data')
        flagdata(vis=msfile_c7,antenna='ea12,ea16')
        applycal(vis=msfile_c7,field='SUN01',\
                 gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                 calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc',\
                 slfcalprefix+'.spw0.G1',slfcalprefix+'.spw1.G1',slfcalprefix+'.spw2.G1',\
                 slfcalprefix+'.spw3.G1',slfcalprefix+'.spw4.G1',slfcalprefix+'.spw5.G1',\
                 slfcalprefix+'.spw6.G1',],\
                 gainfield=['','','','J1347+1217','J1347+1217','J1347+1217','','','','','','',''],\
                 interp=['','','','','','',\
                         'nearest','nearest','nearest','nearest','nearest','nearest','nearest'],\
                 spwmap=[],applymode='calonly',parang=False,flagbackup=True)
        split(vis=msfile_c7, outputvis='sun01_20141101.50ms.cal.ms',\
              field='SUN01',datacolumn='corrected')
    if cal_ms_c7_sml:
        #split(vis=msfile_sun01,outputvis=msfile_c7_sml,timerange='16:42:40~16:43:10',datacolumn='data')
        #flagdata(vis=msfile_c7_sml,antenna='ea12,ea16')
        clearcal(vis=msfile_c7_sml)
        spws=['0','1','2','3','4','5','6','7']
        for spw in spws:
            applycal(vis=msfile_c7_sml,field='SUN01',spw=spw,\
                     gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                     calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc',\
                     slfcalprefix+'.spw'+spw+'.G1'],\
                     gainfield=['','','','J1347+1217','J1347+1217','J1347+1217',''],\
                     interp=['','','','','','','nearest'],\
                     spwmap=[],applymode='calonly',parang=False,flagbackup=True)
        split(vis=msfile_c7_sml, outputvis='SUN01_20141101T164240-164310.50ms.cal.ms',\
              field='SUN01',datacolumn='corrected')
    if cal_ms_c7_med:
        split(vis=msfile_sun01,outputvis=msfile_c7_med,timerange='16:41:00~16:47:00',datacolumn='data')
        flagdata(vis=msfile_c7_med,antenna='ea12,ea16')
        clearcal(vis=msfile_c7_med)
        spws=['0','1','2','3','4','5','6','7']
        for spw in spws:
            applycal(vis=msfile_c7_med,field='SUN01',spw=spw,\
                     gaintable=[calprefix+'.rq',calprefix+'.delay',calprefix+'.bp',\
                     calprefix+'.pha_inf',calprefix+'.amp_inf',calprefix+'.amp_Finc',\
                     slfcalprefix+'.spw'+spw+'.G1'],\
                     gainfield=['','','','J1347+1217','J1347+1217','J1347+1217',''],\
                     interp=['','','','','','','nearest'],\
                     spwmap=[],applymode='calonly',parang=False,flagbackup=True)
        split(vis=msfile_c7_med, outputvis='SUN01_20141101T164100-164700.50ms.cal.ms',\
              field='SUN01',datacolumn='corrected')




