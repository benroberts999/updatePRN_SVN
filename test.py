#!/usr/bin/python3
#Uses python3
import urllib.request
import datetime

################################################################################
def fetchDaysOA(year, day_of_year):
# Function that takes in a year+day, downloads and parses the 'OA' (Operational
# Advisories) files from the web, and return a list in the form:
# [year, month, day, day_of_year, clock1, clock2, ..., clock32].
# Note: there is 1 'clock' entry for each PRN (1-32); eith Rb, Cs, or no.
# 'no' means that PRN was not in use that day.
  
  #work out the actual date from the year+day
  the_date=datetime.date(year, 1, 1) + datetime.timedelta(day_of_year-1)
  month=the_date.month
  day=the_date.day
  
  #fetch the data from the web [python3]:
  url = 'https://www.navcen.uscg.gov/?Do=getAdvisory&advisory='+str(day_of_year)+'&year='+str(year)
  response = urllib.request.urlopen(url)
  data=response.read()
  text = data.decode('utf-8')
  #print (text)
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

  # Form the (string) list of PRNs
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
  clk_list = [e for e in str_clk_list.split(',')]
  clk_list = list(filter(None, clk_list)) #filter any missing points
  #print (clk_list)
  
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


def test():
  import os

  filename="hello.txt"

  if os.path.exists(filename):
    ifile = open(filename, "r")
    line="2000 1 1 1 0"
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

  print(year, day)

  skipped_days=0
  ofile = open(filename, "a")

  while skipped_days<10:
    day += 1
    if day>366:
      day=1
      year+=1
    print(year, day)

    day_OA_line=fetchDaysOA(year,day)
    
    # count the number of "missed days" in a row
    if day_OA_line == "nodata":
      skipped_days += 1
      continue
    else:
      skipped_days = 0

    print("-->",year,"-",day_OA_line[1],"-",day_OA_line[2], sep='')

    current_clk_list=day_OA_line[4:]

    if prev_clk_list != current_clk_list:
      for i in day_OA_line:
        ofile.write(str(i)+" ")
      ofile.write("\n")
      prev_clk_list=current_clk_list

  ofile.close()



#print(fetchDaysOA(2000,3))

test()














