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
  import os
  import datetime

  #filename="allClockSwapsByDay.out"

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
    year=mylist[0]
    day=mylist[3]+1
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
      break
    
    print("Fetching OA for:", year, day)
    
    # Fetch and parse the OA file (func defined above)
    day_OA_line=fetchDaysOA(year,day)
    
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



  ### Don't delete this yet! - we'll need it to convert the dates back!
  #jan_1_1970 = datetime.date(1970, 1, 1)
  #print(jan_1_1970)
  #d1 = datetime.date(2005, 5, 5)
  #delta = d1 - jan_1_1970
  #print (delta.days)

  #date_format="%Y-%m-%d"
  #a_day="2005-5-5"
  #d1=datetime.datetime.strptime(a_day,date_format)
  #delta = d1.date() - jan_1_1970
  #print (delta.days)

  #abc = jan_1_1970+datetime.timedelta(delta.days)
  #print (abc)

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
  from operator import itemgetter
  prn_gps_list=sorted(prn_gps_list, key=itemgetter(i_prn,i_date_i))

#  for el in prn_gps_list:
#    print(el)
  
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

#print(fetchDaysOA(2006,254))

#import datetime

#tod=datetime.datetime.now().date()
#jan_1_1970 = datetime.date(1970, 1, 1)

#print (tod.year)

#if(jan_1_1970 < tod):
#  print ('yes')
#else:
#  print('no')




################################################################################



filename="allClockSwapsByDay.out"

#formSwapsByDay(filename)

prn_gps=getPRNGPS()

oa_map=getOaPrnList(filename)

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

#print(checkOA(15000,4))

prn_gps_gpsdm=[]

for line in prn_gps:
  #print(line)
  start_date = line[0]
  end_date = line[1]
  svn = line[2]
  prn = line[3]
  block = line[4]
  orb = line[5]
  clock_prngps = line[6]
  while(True):
    oa_out = checkOA(start_date, prn)
    if oa_out[0] == 1: #worked!
      oa_start=oa_out[1]
      oa_end=oa_out[2]
      oa_clock = oa_out[3]
      if oa_end >= end_date:
        new_line = [start_date, end_date, svn, prn, block, orb, oa_clock]
        prn_gps_gpsdm.append(new_line)
        break
      else:
        new_line = [start_date, oa_end, svn, prn, block, orb, oa_clock]
        prn_gps_gpsdm.append(new_line)
        start_date = oa_end + 1
        continue
    elif oa_out[1] != 0:
      the_end = oa_out[1]
      the_clock = clock_prngps + " ! Not on OA"
      new_line = [start_date, the_end, svn, prn, block, orb, the_clock]
      prn_gps_gpsdm.append(new_line)
      start_date = the_end + 1
      continue
    else:
      the_clock = clock_prngps + " ! Not on OA"
      new_line = [start_date, end_date, svn, prn, block, orb, the_clock]
      break
        
    
for el in prn_gps_gpsdm:
  print(el)























































