#!/usr/bin/python3


#Full URL: ftp://ftp.igs.org/pub/station/log/
#Fetches the GIS station logs from igs.org, parses them, and makes a PRN_GPS-like
#lookup file, to match the station with the clock-type.

# NB: "BRUX" issue? e.g., EXTERNAL 5071A CESIUM

################################################################################
def findall(a_string, sub):
# Function that finds every instance of a substring in a string, 
# returns a list of the locations (integers)
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
################################################################################


################################################################################
def progressBar(current, total, bar_width):
# A progress bar
  import sys
  perc = current/(total-1)
  prog = int(perc*bar_width)
  sys.stdout.write("[%s] %s\r" % (" " * bar_width, str(int(perc*100))+'%'))
  sys.stdout.write("[")
  for i in range(prog):
    sys.stdout.write("=")
  sys.stdout.flush()
  sys.stdout.write("\r")
  if(current >= total-1):
    sys.stdout.write("\n")
################################################################################




################################################################################
def getStaList(base_url,path_url):
# Reads and parses all the IGS station log files
  from ftplib import FTP
  import urllib.request
  from io import StringIO
  
  # Use ftp to log into the server, and get a list of all log files:
  ftp = FTP(base_url)
  ftp.login()
  ftp.cwd(path_url)
  log_files = ftp.nlst()

  # Goes through each log file, one at a time
  out_file = []
  total = len(log_files)
  print("Reading in the IGS station logs")
  print("Total of",total,"files:")
  n=0;
  for sta_log in log_files:
    
    progressBar(n,total,50)
    n+=1 #only used for the progress bar
    
    # Fetch the file into a string:
    # Probably a way to do this using ftp? whatever..
    response = urllib.request.urlopen('ftp://'+base_url+path_url+sta_log)
    data=response.read()
    text = data.decode('utf-8',errors='ignore')

    # Find the station name
    x = text.find("Four Character ID")
    start = text.find(":",x)
    end = text.find("\n",start)
    name=text[start+1:end+1]
    name=name.replace("\n",'') # kill trailing end-line
    name=name.replace(' ','') # kill trailing end-line

    # Find the relevant section of the file:
    # There is one such block for each "swap"
    out = findall(text, 'Standard Type')
    for i in out:
      
      #Find the standard (clock type)
      start = text.find(":",i)
      end = text.find("\n",start)
      temp=text[start+1:end+1]
      standard_list = [s for s in temp.split()]
      if len(standard_list) == 0:
        standard_list = ['X','X']
      elif len(standard_list) == 1:
        standard_list.append('X')
      
      # Quit this log file once we get past actual data lines
      # Alternatively: Look for '6.x', make sure we're before that character!
      if standard_list[0] == "(INTERNAL":
        break
      
      # Sometimes a few different words here. Only last word matters??
      if len(standard_list)>2:
        fin = len(standard_list)-1;
        st1 = ""
        #for s in range(fin):
        #  st1 += standard_list[s]+" "  ## XXX ???
        st1 = standard_list[0]
        st2 = standard_list[fin]
        standard_list = [st1, st2]
      
      # Sometimes internal/external not given, so clock erroniously comes first:
      if standard_list[0] in ("H-MASER", "RUBIDIUM", "Rubidium", "CESIUM", "QUARTZ"):
        temp = standard_list[1]
        standard_list[1] = standard_list[0]
        standard_list[0] = temp
      
      # Find the effective dates
      x = text.find("Effective Dates",i);
      start = text.find(":",x)
      end = text.find("\n",start)
      temp=text[start+1:end+1]
      temp=temp.replace("\n", "") # kill trailing end-line
      temp=temp.replace(" ", "") # kill trailing end-line
      temp=temp.replace("(", "") # kill leading '(' (only appears rarely)
      date_list = [s for s in temp.split('/')]
      
      # Quit this log file once we get past actual data lines
      # Alternatively: Look for '6.x', make sure we're before that character!
      if date_list[0]=="CCYY-MM-DD":
        break
      
      # Fix the formatting to make consistent
      # 'c' means assignment still current
      if len(date_list) == 1:
        date_list.append('?')
      if (date_list[1] == 'CCYY-MM-DD'):
        date_list[1] = 'c'
      
      # Remove trailing time-zone crap that appears sometimes
      if len(date_list[0])>10:
        date_list[0] = date_list[0][:10]
      if len(date_list[1])>10:
        date_list[1] = date_list[1][:10]
      
      # Find and store any "notes"
      x = text.find("Notes",i);
      start = text.find(":",x)
      end = text.find("\n6.",start)
      notes=text[start+1:end-1]
      notes=notes.replace("\n", " ") # kill trailing end-line
      notes=notes.replace('  ','') # kill trailing end-line
      
      #Add this line to the output list
      outline = [name] + standard_list + date_list + [notes]
      out_file.append(outline)
      
  return out_file
################################################################################

################################################################################
def writeStaList(out_file, out_name):
# Just formats and writes the list to file
  import datetime
  from operator import itemgetter

  print("Writing the file to disk")

  ofile = open(out_name, "w")

  # Sorts the list by name, then date
  out_file=sorted(out_file, key=itemgetter(0,3))

  # Get todays  date, write to file.
  today = datetime.datetime.now().date()
  ofile.write(str(today)+"\n")

  #Write some header stuff to file
  header ="! IGS Station log summary.\n"
  header+="! Comment lines start with '!'\n"
  header+="! End date of 'c' mean current\n"
  header+="! Last fetched: "+str(today)+"\n!\n"
  header+="! Name  Standard         Clock  start-date    end-date   ! Notes\n"
  ofile.write(header)

  #Format the output data (make look nice) and write to file
  for line in out_file:
    ofile.write('%6s %9s %13s %11s %11s   !%s\n' % tuple(line))
  ofile.close()
################################################################################


base_url = 'ftp.igs.org'
path_url = '/pub/station/log/'
out_name = "STA_CLOCK_GPSDM.txt"

sta_list = getStaList(base_url,path_url)
writeStaList(sta_list,out_name)








































