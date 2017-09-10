#!/usr/bin/python3
#Uses python3

################################################################################
def fetchDaysOA(year, day_of_year):
# Function that takes in a year+day, downloads and parses the 'OA' (Operational
# Advisories) files from the web, and return a list in the form:
# [year, month, day, day_of_year, clock1, clock2, ..., clock32].
# Note: there is 1 'clock' entry for each PRN (1-32); eith Rb, Cs, or no.
# 'no' means that PRN was not in use that day.
  import urllib.request
  import datetime

  #work out the actual date from the year+day
  the_date=datetime.date(year, 1, 1) + datetime.timedelta(day_of_year-1)
  month=the_date.month
  day=the_date.day
  
  #fetch the data from the web [python3]:
  url = 'https://www.navcen.uscg.gov/?Do=getAdvisory&advisory='+str(day_of_year)+'&year='+str(year)
  response = urllib.request.urlopen(url)
  data=response.read()
  text = data.decode('utf-8')
  #print (text,"\n") #to test
  #print (data,"\n")
  #print (len(text),"\n")
  if text=="ERROR: No such file" or text=='' or len(text)<100:
     return "nodata"

  # Function that finds every instance of a substring in a string, 
  # returns a list of the locations (integers)
  def findall(a_string, sub):
    result = []
    k = 0
    while k < len(a_string):
        k = a_string.find(sub, k)
        if k == -1:
            return result
        else:
            result.append(k)
            k += 1 #change to k += len(sub) to not search overlapping results
    return result

  # Lists of the start positions of each relevant data line:
  prn_index_list=findall(text,"PRNS")
  clk_index_list=findall(text,"CLOCK ")

  # Form the list of PRNs
  str_prn_list=""
  for i in prn_index_list:
    end=text.find("\n",i)
    temp=text[i+4:end+1]
    temp=temp.replace(" ", "")  #kill white space
    temp=temp.replace("\r", "") #kills the carrige return/newlines
    temp=temp.replace("\n", "")
    str_prn_list=str_prn_list+temp+"," #sepparate new lines with ","
  #print(str_prn_list)
  # Parse the "," seperated values, and convert to integers
  prn_list = [int(e) if e.isdigit() else e for e in str_prn_list.split(',')]
  prn_list = list(filter(None, prn_list)) #filter any missing points
  #print (prn_list,"\n")
  
  #Forms the list of clocks
  str_clk_list=""
  for i in clk_index_list:
    beg=text.find(":",i)
    end=text.find("\n",beg)
    temp=text[beg+1:end+1]
    temp=temp.replace(" ", "")
    temp=temp.replace("\r", "") #kills the carrige return/newlines
    temp=temp.replace("\n", "")
    temp=temp.replace("RB", "Rb") #Change case to match PRN_GPS file
    temp=temp.replace("CS", "Cs")
    str_clk_list=str_clk_list+temp+","
  # Parse the "," seperated values:
  tmp_clk_list = [e for e in str_clk_list.split(',')]
  tmp_clk_list = list(filter(None, tmp_clk_list)) #filter any missing points
  clk_list = list(s[:2] for s in tmp_clk_list) #kills any trailing junk
  #print ("\n",clk_list,"\n")
  
  #Safety check. Program will fail if the format of one of the OA files
  # is significantly different. The program will output an error messaage, but
  # then just hope that that day was not important...
  if len(prn_list) != len(clk_list):
    print("FAILURE: prn and clk don't match for", the_date, "(",day_of_year,")", 
          len(prn_list), "=/=", len(clk_list))
    return "nodata"  #??
  
  # make sure following loop cannot extend past limit of list
  while len(prn_list) < 32:
    prn_list.append(0)
  
  ## Check if there are any duplicate PRNs! If so, deletes the second one.
  # I assume that there is never data for these days? If there is, only 1 day..?
  # nb: sometimes duplicates of 'zero' at end, see above!
  for i in range (len(prn_list)): 
     #note: len(prn_list) changes when items deleted!!
    if i==0 or i==len(prn_list):
      continue
    if prn_list[i]==prn_list[i-1] and prn_list[i] != 0:
      del prn_list[i]
      del clk_list[i]
  
  #Loops through each possible PRN (1-32), forms the final output list
  full_lst=[year, month, day, day_of_year]
  j=0
  for i in range (1,32+1):
    if prn_list[j] == i:
      full_lst.append(clk_list[j])
      j+=1
    else:
      full_lst.append("no")

  return full_lst
################################################################################

## NOTE:
#-A few of the days don't have a new line after tha line of clocks,
#e.g., 2011,234 [22 Aug]:
#   BLOCK II: PRNS 29, 30, 31, 32
#   PLANE   : SLOT C1, B5, A2, E5
#   CLOCK   :      RB, RB, RB, RB 2. CURRENT ADVISORIES AND FORECASTS :



################################################################################
def formSwapsByDay(filename):
#Function that forms the "allClockSwapsByDay" file. This file contains one
# line for each day that a clock was swapped (between Cs, Rb, or no).
# The format of each line of the file is:
#   year month day day_of_year Clock1 clock2 ..... clock32
# There is one clock assignment for each PRN (1-32); can be 'no' if no clock
# It forms this file by downloading the operational advisories (OA) files from the web
# Note: it saves each new 'swap' in this file, to avoid having to download all
# the OAs each time. It checks the existing file first, and starts where it left off.
# Program will continue to run untill it cannot find/open 25 OA files in a row
# After that, program assumes this is because we got to the end of the files,
# so it finishes. Also, stops once it gets to todays date!
# When it gets to todays date, it writes a line to the file even if there weren't
# any swaps (writes last successful OA download.
# This is just to save time next time!
  import os
  import datetime

  # Check if file already exists. If so, reads in the last date that we have 
  # info for. If not, start at January 2000 [first 30s clk file is may 2000].
  if os.path.exists(filename):
    ifile = open(filename, "r")
    line="2000 1 1 1 0" #In case file exists, but is empty
    for line in ifile:
        pass
    last = line
    mylist = [int(e) if e.isdigit() else e for e in last.split()]
    prev_clk_list=mylist[4:]
    prev_year=year=mylist[0]
    prev_day=day=mylist[3]  #? why +1?
  else:
    year=2000
    day=1
    prev_clk_list=[]
  #END if
  #print(year, day)
  
  #Open the file for "append" output
  skipped_days=0
  ofile = open(filename, "a")
  
  # Get todays  date (no point looking after this!)
  today = datetime.datetime.now().date()

  #start with a blank list:  
  last_OA_day=[]
  
  #Keep going until we have not found 25 OA files in a row
  while skipped_days<25:
    day += 1
    if day>366:
      day=1
      year+=1
    
    #exit early if gone past today.
    the_date = datetime.date(year, 1, 1)+datetime.timedelta(days=(day-1))
    if(the_date > today):
      print("Reached todays date! Finished fetching OAs")
      if(len(last_OA_day)>10): #i.e., if it holds actual line
        for i in last_OA_day:
          ofile.write(str(i)+" ")
        ofile.write("\n")
      break
    
    print("Fetching OA for:", year, day)
    
    # Fetch and parse the OA file (func defined above)
    day_OA_line=fetchDaysOA(year,day)
    
    #Store last successful OA download:
    if(len(day_OA_line)>10):
      last_OA_day=day_OA_line
    
    # count the number of "missed days" in a row
    if day_OA_line == "nodata":
      skipped_days += 1
      continue
    else:
      skipped_days = 0

    print("-->",year,"-",day_OA_line[1],"-",day_OA_line[2], sep='')
    
    # Checks if there has been a change in any of the clock assignments since
    # last line (yesterday). If so, write to file.
    current_clk_list=day_OA_line[4:]
    if prev_clk_list != current_clk_list:
      for i in day_OA_line:
        ofile.write(str(i)+" ")
      ofile.write("\n")
      prev_clk_list=current_clk_list
      prev_year = day_OA_line[0]
      prev_day = day_OA_line[3]
  #END while
    
  ofile.close()
################################################################################



################################################################################
def getPRNGPS():
#Program downloads the latest version of the PRN_GPS.gz file from JPL/NASA.
#This file has the correct PRN<->SVN mappings, but often has incorrect clock
#assignments.
#Parses this file into a list, which is in the format:
#  initial_date final_date svn prn block orbit clock
#The dates are given in number of days since 1/1/1970.
#This list is sorted by prn, then by date, and returned.
  import urllib.request
  import os
  import gzip
  import io
  import datetime
  from operator import itemgetter
  
  url='ftp://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz'
  file_name='PRN_GPS.gz'
  
  #Try to download the PRN_GPS.gz file from JPL/NASA:
  try:
    urllib.request.urlretrieve(url, file_name)
  except Exception:
    print('X!  Error: Couldnt donwload PRN_GPS file')
    print("X!  Will continue, using existing file (if it exists)")
    print("X!  But you should check manually for an updated PRN_GPS file!")

  #If file exists, read it in. Note: little stringe becaus it is g-zipped
  if os.path.exists(file_name):
    inF = gzip.open(file_name, 'rb') # what is 'rb' ?
    inF_r = inF.read().decode('utf-8')
    inF.close()
    in_prn_gps = io.StringIO(inF_r)
  else:
    print("X! Don't have PRN_GPS file! Can't run!")
    exit()

  #each complete row has 7 entries. There are some rows with fewer
  #than 7, but we don't care about them, so they can be dropped
  num_rows=7

  # Read through the PRN_GPS file, read each relevant row into a list:
  prn_gps_list=[]
  first_line = True
  for line in in_prn_gps:
    if first_line: #skip the first line
      first_line=False
      continue
    out = [int(e) if e.isdigit() else e for e in line.split()]
    if len(out)==num_rows:
      prn_gps_list.append(out)
    elif len(out)>num_rows:
      #throw away the extra trailing junk:
      prn_gps_list.append(out[:num_rows]) 

  # Date formats. Used by next block:
  date_format="%Y-%m-%d"
  jan_1_1970 = datetime.date(1970, 1, 1)
  
  # We will reference all dates as number of days since 1/1/1970, to make
  # comparing two days as easy as possible. Will have to be converted back!
  # This loop does the conversion.
  # Note: PRN_GPS file has date='0000' when this is the current assignment!
  for el in prn_gps_list:
    str_date_i=el[0]
    date_i=datetime.datetime.strptime(str_date_i,date_format)
    days_i = date_i.date() - jan_1_1970
    el[0]=days_i.days
    str_date_f=el[1]
    if str_date_f==0: #'0' in file means still current (i.e. beyond present day)
      el[1]=99999   #just really big number. (remember to convert back later!)
    else:
      date_f=datetime.datetime.strptime(str_date_f,date_format)
      days_f = date_f.date() - jan_1_1970
      el[1]=days_f.days

  #for el in prn_gps_list:
  #  print(el)

  #Index identifiers for the columns
  i_date_i = 0
  i_date_f = 1
  i_svn = 2
  i_prn = 3
  i_blk = 4
  i_orb = 5
  i_clk = 6

  # Sorts the list (by PRN, then by date)
  prn_gps_list=sorted(prn_gps_list, key=itemgetter(i_prn,i_date_i))
  
  return prn_gps_list
################################################################################

################################################################################
def getOaPrnList(filename):
#This program reads in the "allClockSwapsByDay" file that contains one line
#for each day that there was a clock assignment change. This file is created by
#the formSwapsByDay() function [which calls the fetchDaysOA() function], and
#uses official Operational Advisories data.
#I forms a list, that is in the form:
#  initial_date final_date PRN clock
#that says what clock was assignment to which prn for which period.
#This list is already in order by prn then by date.
#This list is returned.
  import os
  import datetime

  #Reads in the allClockSwapsByDay if it exists.
  if os.path.exists(filename):
    ifile = open(filename, "r")
  else:
    print("File", filename, "does not exist!?? Can't run.")
    exit()

  # Date formats. Used by next block:
  date_format="%Y-%m-%d"
  jan_1_1970 = datetime.date(1970, 1, 1)

  # Form the "swap list" from the swap file.
  # List is in format initial_date clock1, clock2, ..., clock32
  # One clock assignment (Rb/Cs/ns) for each PRN (1-32).
  # Date is given as number of days since 1/1/1970
  swap_list=[]
  for line in ifile:
    line_list = [int(e) if e.isdigit() else e for e in line.split()]
    clk_list = line_list[4:] #first 4 elements contain date
    yy=line_list[0]
    mm=line_list[1]
    dd=line_list[2]
    the_date = datetime.date(yy, mm, dd)
    days = the_date - jan_1_1970 #convert to days since 1/1/70
    line_list = [days.days] + clk_list
    swap_list.append(line_list)

  #for el in swap_list:
  #  print(el)

  # Forms the "OA_PRN_CLK" list - like the PRN_GPS list, lists clock<->PRN 
  # assignments.
  # For each prn, finds when the clock swapped, then record the date range to list
  oa_prn_clk_list=[]
  for prn in range (1,32+1):
    date_i = swap_list[0][0]
    prev_date = date_i
    prev_clock = swap_list[0][prn]
    for el in swap_list:
      this_date = el[0]
      this_clock = el[prn]
      if this_clock != prev_clock:
        date_f = this_date - 1
        if prev_clock != "no":
          oa_prn_clk_list.append([date_i, date_f, prn, prev_clock])
        date_i = this_date
      prev_date = this_date
      prev_clock = this_clock
    # Got to the end of the file, clock currently has this assignment:
    # '99999' just means 'very big number' - will be converted later!
    if prev_clock != "no":
      oa_prn_clk_list.append([date_i, 99999, prn, prev_clock])

  #for el in oa_prn_clk_list:
  #  print(el)

  return oa_prn_clk_list
################################################################################



################################################################################
def generatePrnGpsDm(prn_gps, oa_map):
#Program takes in the prn_gps mapping list, and the OA mapping list to form the
#correct prn-svn-clock mapping list, which is returned.
# Returned list has same format as prn_gps list:
#    initial_date final_date SVN PRN Block Orbit clock
#(dates given in number of days since 1/1/1970.
#Gets each PRN-SVN mapping line from prn_gps, then loops through the OA list 
#looking for the corresponding PRN-Clock mapping. Note: the start and end dates
#don't necisarily match, so the program takes that into account, and adds new 
#lines when needed.
#There is never a clock in use that is not listed in the PRN_GPS file, so it does
#not add any lines in the case that there is a mapping in OA that doesn't exist 
#in PRN_GPS.
#However, there sometimes are occasions where there is a PRN_GPS entry, that has
#no corresponding OA mapping. In this case, it assumes PRN_GPS was correct.
#This assumption is not always correct, but when not, it must be dealt with 
#"manually", using the 'corrections' routine.
# In these cases, appends a comment "! Not on OA' to the list.
#(Most of these don't have JPL data anyway, but some do!)
#
# STILL NEEDS TO BE CHECKED MANUALLY!

  # Small function that loops through the OA list, and finds the clock assignment
  # for a given PRN and day. Returns a list.
  # First element of list is 1 if it successfully found the mappings
  #  => [1, start_date, end_date, clock]
  # If not, it finds the first date in the future that the map exists, and
  # returns ==> [0, last_day_map_doesn't_exist]
  # If it couldn't even find that, means it isn't on oa. Returns [0,0]
  def checkOA(start_date, prn):
    for line in oa_map:
      if line[2] == prn:
        oa_start = line[0]
        oa_end = line[1]
        clock = line[3]
        if oa_start <= start_date and oa_end >= start_date:
          # found!
          return [1,oa_start,oa_end,clock]
    #got to end of oa_map. therefore, didn't find!
    for line in oa_map:
      if line[2] == prn:
        oa_start = line[0]
        clock = line[3]
        if oa_start > start_date:
          #First mapping we have!
          #Return last date that ISN'T in oa file! (hence '-1')
          return [0,oa_start-1]
    #If we get here, didn't find it at all? Just Use prn_gps
    return [0,0]

  # Output list:
  prn_gps_gpsdm=[]
  
  # For each line (and each PRN) in the input prn_gps list, find the clock
  # assignment using the OA list, work out the date range that the mappings are
  # valid, and write out the results. Note: If a mapping is not found in the OA
  # files, assumes the PRN_GPS file was correct.
  for line in prn_gps:
    start_date = line[0]
    end_date = line[1]
    svn = line[2]
    prn = line[3]
    #if prn!=1: continue
    block = line[4]
    orb = line[5]
    clock_prngps = line[6]
    #print("\n",line,"\n")
    while(True):
      oa_out = checkOA(start_date, prn)
      if oa_out[0] == 1: #worked!
        oa_start=oa_out[1]
        oa_end=oa_out[2]
        oa_clock = oa_out[3]
        if oa_end >= end_date:
          new_line = [start_date, end_date, svn, prn, block, orb, oa_clock]
          prn_gps_gpsdm.append(new_line)
          #print("a: ",new_line)
          break
        else:
          new_line = [start_date, oa_end, svn, prn, block, orb, oa_clock]
          prn_gps_gpsdm.append(new_line)
          start_date = oa_end + 1
          #print("b: ",new_line)
          continue
      elif oa_out[1] != 0:
        the_end = oa_out[1]
        the_clock = clock_prngps + "   ! Not on OA"
        if the_end >= end_date:
          the_end = end_date
          new_line = [start_date, the_end, svn, prn, block, orb, the_clock]
          prn_gps_gpsdm.append(new_line)
          #print("c: ",new_line)
          break;
        else:
          new_line = [start_date, the_end, svn, prn, block, orb, the_clock]
          prn_gps_gpsdm.append(new_line)
          start_date = the_end + 1
          #print("d: ",new_line)
          continue
      else:
        the_clock = clock_prngps + "   ! Not on OA"
        new_line = [start_date, end_date, svn, prn, block, orb, the_clock]
        prn_gps_gpsdm.append(new_line)
        #print("e: ",new_line)
        break
        
  return prn_gps_gpsdm
################################################################################

################################################################################
def writePrnGpsGpsdm(prn_gps_gpsdm, out_filename):
  import datetime
  from operator import itemgetter
    
  ofile = open(out_filename, "w")
  
  #Used to convert from 'days since 1/1/70' to date
  jan_1_1970 = datetime.date(1970, 1, 1)

  # Sorts the list (by SVN, then by date)
  prn_gps_gpsdm=sorted(prn_gps_gpsdm, key=itemgetter(2,0))

  # Get todays  date, write to file.
  today = datetime.datetime.now().date()
  ofile.write(str(today)+"\n")

  #Write some header stuff to file
  header ="! Our updated PRN_GPS file.\n"
  header+="! Combines JPL PRN_GPS file (that has accurate PRN-SVN mapptings)\n"
  header+="! with the US-NavCen Operational Advisories (OAs)\n"
  header+="! (that contain accurate PRN-Clock mappings.\n"
  header+="! Comment lines start with '!'\n"
  header+="! Last fetched: "+str(today)+"\n!\n"
  header+="! init. date   fin. date  SVN  PRN  BLK  ORB  CLK    Note\n"
  ofile.write(header)
  
  #Format the output data (make look nice) and write to file
  for line in prn_gps_gpsdm:
    date_i = "  "+str(jan_1_1970+datetime.timedelta(days=line[0]))+"  "
    if(line[1]==99999):
      date_f="0000      "+"   "
    else:
      date_f = str(jan_1_1970+datetime.timedelta(days=line[1]))+"   "
    if line[2]<10 :
      svn = " "+str(line[2])+"   "
    else:
      svn = str(line[2])+"   "
    if(line[3]<10):
      prn=" "+str(line[3])+"  "
    else:
      prn=str(line[3])+"  "
    if(line[4]=="I"):
      block = "I  "+"  "
    elif(line[4]=="II"):
      block = "II "+"  "
    else:
      block = line[4]+"  "
    orbit = "orb"+"  "  #Don't need orbits, but file format needs to match
    clock = line[6]+"  "
    outline = date_i + date_f + svn + prn + block + orbit + clock + "\n"
    ofile.write(outline)
  ofile.close()
################################################################################



################################################################################
def getExceptions(prn_gps_gpsdm, exceptions_fn):
  import os
  import datetime
  from operator import itemgetter
    
  #Reads in the allClockSwapsByDay if it exists.
  if os.path.exists(exceptions_fn):
    ifile = open(exceptions_fn, "r")
  else:
    print("bah")
   #return

  # Date formats. Used by next block:
  date_format="%Y-%m-%d"
  jan_1_1970 = datetime.date(1970, 1, 1)

  for line in ifile:
    #parse the line from the exceptions file to get correct format
    line_list = [int(e) if e.isdigit() else e for e in line.split()]
    if line_list[0][0]=="!":
      continue
    note = " ".join(line_list[7:])
    line_list = line_list[:7]
    line_list.append(note)
    #make list in correct format:
    i_date = [int(e) for e in line_list[0].split("-")]
    yi=i_date[0]
    mi=i_date[1]
    di=i_date[2]
    i_date = datetime.date(yi, mi, di)
    #convert to days since 1/1/70:
    i_days = i_date - jan_1_1970
    if line_list[1]==0:
      f_days=99999
      line_list = [i_days.days] + [f_days] + line_list[2:]
    else:
      f_date = [int(e) for e in line_list[1].split("-")]
      yf=f_date[0]
      mf=f_date[1]
      df=f_date[2]
      f_date = datetime.date(yf, mf, df)
      f_days = f_date - jan_1_1970
      line_list = [i_days.days] + [f_days.days] + line_list[2:]
    #print(line_list)
    di = line_list[0]
    df = line_list[1]
    svn= line_list[2]
    prn= line_list[3]
    blk= line_list[4]
    orb= line_list[5]
    clk= line_list[6]
    note=line_list[7]
    #outlist = [di,df,svn,prn,blk,orb,clk+"   ! "+note]
    #print(outlist)
    #for prngps_line in prn_gps_gpsdm:
    # Re-sorts the list (by PRN, then by date)
    prn_gps_gpsdm=sorted(prn_gps_gpsdm, key=itemgetter(3,0))
    orig_length = len(prn_gps_gpsdm) #will add entries (to the end)!
    for l in range (orig_length): #l is the index!
      prngps_line = prn_gps_gpsdm[l]
      #print(prngps_line)
      odi  = prngps_line[0]
      odf  = prngps_line[1]
      osvn = prngps_line[2]
      oprn = prngps_line[3]
      oblk = prngps_line[4]
      oorb = prngps_line[5]
      oclk = prngps_line[6]
      # Check: if we're at end of file without a 'break' means not yet found:
      if oprn>prn:
        print("here")
        #Moved passed the correct PRNs without finding a match, means
        #we shuold just write out the whole new entry:
        outlist = [di,df,svn,prn,blk,orb,clk+"   ! "+note]
        prn_gps_gpsdm.append(outlist)
        break
      if oprn != prn: continue #compare PRNs
      if df<odi:
        #add new entry:
        outlist = [di,df,svn,prn,blk,orb,clk+"   ! "+note]
        prn_gps_gpsdm.append(outlist)
        break
      elif di<odi and df>=odi and df<odf:
        #modify existing entry:
        prngps_line[0] = df+1
        prn_gps_gpsdm[l] = prngps_line
        # and add new entry:
        outlist = [di,df,svn,prn,blk,orb,clk+"   ! "+note]
        prn_gps_gpsdm.append(outlist)
        break
      elif di<odi and df >= odf:
        #modify existing:
        prngps_line[0] = di
        prngps_line[2] = svn
        prngps_line[3] = prn
        prngps_line[4] = blk
        prngps_line[5] = orb
        prngps_line[6] = clk+"   ! "+note
        prn_gps_gpsdm[l] = prngps_line
        # Update current exception line, go to next prn line:
        di = odf+1
        if df>=di:
          continue
        else:
          break
      elif di>=odi and di<=odf and df<=odf:
        #modify existing:
        prngps_line[0] = di
        prngps_line[1] = df
        prngps_line[2] = svn
        prngps_line[3] = prn
        prngps_line[4] = blk
        prngps_line[5] = orb
        prngps_line[6] = clk+"   ! "+note
        prn_gps_gpsdm[l] = prngps_line
        # add two new lines (with original assignments):
        if di-1>=odi:
          outlist = [odi,di-1,osvn,oprn,oblk,oorb,oclk]
          prn_gps_gpsdm.append(outlist)
        if odf>=df+1:
          outlist = [df+1,odf,osvn,oprn,oblk,oorb,oclk]
          prn_gps_gpsdm.append(outlist)
        break
      elif di>=odi and di<=odf and df>odf:
        #Add new entry:
        if di-1>=odi:
          outlist = [odi,di-1,osvn,oprn,oblk,oorb,oclk]
          prn_gps_gpsdm.append(outlist)
        #Modify existing:
        prngps_line[0] = di
        prngps_line[1] = odf
        prngps_line[2] = svn
        prngps_line[3] = prn
        prngps_line[4] = blk
        prngps_line[5] = orb
        prngps_line[6] = clk+"   ! "+note
        prn_gps_gpsdm[l] = prngps_line
        # Update current exception line, go to next prn line:
        di = odf+1
        if df>=di:
          continue
        else:
          break
      #End if
    #End for (loop over PRNs)
  #End for (loop over exceptions)

  # Re-sorts the list (by PRN, then by date), returns it
  return sorted(prn_gps_gpsdm, key=itemgetter(3,0))
################################################################################


filename="allClockSwapsByDay.out"
out_filename = "PRN_GPS_GPSDM_test.txt"
exceptions_fn = "exceptions.in"

# Check the web for any OA updates, form allClockSwapsByDay.out file.
formSwapsByDay(filename)

# Read in the allClockSwapsByDay.out file, parse into list
oa_map=getOaPrnList(filename)

# Download the latest PRN_GPS from JPL, read/parse it into list
prn_gps=getPRNGPS()

# 
prn_gps_gpsdm = generatePrnGpsDm(prn_gps,oa_map)

prn_gps_gpsdm = getExceptions(prn_gps_gpsdm,exceptions_fn)

writePrnGpsGpsdm(prn_gps_gpsdm,out_filename) 




























