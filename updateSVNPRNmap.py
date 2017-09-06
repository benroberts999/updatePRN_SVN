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
  #print (text) #to test
  if text=="ERROR: No such file":
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
  #print (prn_list)
  
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
def formSwapsByDay():
#Function that forms the "allClockSwapsByDay" file. This file contains one
# line for each each that a clock was swapped (between Cs, Rb, or no).
# The format of each line of the file is:
#   year month day day_of_year Clock1 clock2 ..... clock32
# There is one clock assignment for each PRN (1-32); can be 'no' if no clock
# It forms this file by downloading the operational advisories (OA) files from the web
# Note: it saves each new 'swap' in this file, to avoid having to download all
# the OAs each time. It checks the existing file first, and starts where it left off.
# Program will continue to run untill it cannot find/open 25 OA files in a row
# After that, program assumes this is because we got to the end of the files,
# so it finishes.
  import os

  filename="allClockSwapsByDay.txt"
  
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
  
  #Keep going until we have not found 10 OA files in a row
  while skipped_days<25:
    day += 1
    if day>366:
      day=1
      year+=1
    print(year, day)
    
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


#print(fetchDaysOA(2012,193))

formSwapsByDay()














