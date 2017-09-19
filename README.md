# Update GPS satellite and station clock assignments

Two programs. Uses a few python3 features.

**updateSVNPRN.py**:

Uses the JPL/NASA PRN_GPS file and the USNavCen operational advisories to 
create a new file, **PRN_GPS_GPSDM.txt**, 
that contains the full correct PRN-SVN-Clock mappings. 
This file is in roughly the same format as the original PRN_GPS file.
Also takes in an optional 'exceptions.in' file, where we can manually add clock
assignments that will over-ride those from PRN_GPS and OA.
When the end-date is '0000', means clock assignment is current.

Format is:
 * start-date end-date SVN PRN BLK ORB CLK Note

**igsStationLogs.py**

Uses the IGS station logs, from ftp://ftp.igs.org/pub/station/log/, 
to creat a `PRN_GPS'-like file that stores which station was using what kind
of clock on what days.
Output file is called: **STA_CLOCK_GPSDM.txt**.
When the end-date is 'c', means clock assignment is current.

Format is:
 * Name Standard Clock start-date end-date ! Notes

********************************************************************************

## Update PRN_GPS file to map PRN to SVN & Clock

**updateSVNPRN.py**

### PRNs, SVNs, Clocks, and Operational Advisories

Each operational GPS satellite has a PRN (PseudoRandom Noise code).
This is a label 1-32 (like a 'slot' in the GPS constellation).
On any given day, only one satellite has each PRN, however, the PRN assigned
to any specific satellite may change several times over the life of the 
satellite.
Each indevidual sattelite also has a unique identifier, called an SVN (Space
Vehicle Number), which never changes.
Also, each sattelite typically has both a Rb and a Cs clock on board, only one 
of which is transmitting at any given time.

The JPL bias data files list the data labelled by PRN (not SVN). They also don't
state which clock type (Rb/Cs) was in use.
To perform any analysis, however, we need to know which indevidual satellite
we are looking at, and what type of clock it is using.

JPL supplies a file, PRN_GPS, that maps each PRN to the SVN for a given day.
Available:
 * ftp://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz

This file also ostensibly states which clock (Rb or Cs) was in use that day.
The PRN-SVN mappings are accurate, however, the clock mappings are known to be
largely wrong.

The US Navigation Center makes available so-called operational advisory
(GPS OPSADVISORIES) files: 
 * https://www.navcen.uscg.gov/?Do=gpsArchives

There is one such file for every single day.
These files state which clock was being used by each PRN on that day, but do
not state which SVN the satellite is.
For the most part, these files accurately record the clock-PRN mappings.*

This program reads both the JPL PRN_GPS file, to determine the PRN-SVN mappings,
and the USNavCen operational advisory files, to determine the PRN-clock mappings.
It combines these two lists to form a new list that has the full correct
PRN-SVN-Clock mappings. It outputs this list in a new file, called
PRN_GPS_GPSDM.txt, that is in roughly the same format as the original PRN_GPS 
file.
New file is ordered by SVN (then date), has format:
 *  initialDate finalDate SVN PRN Block Orbit Clock !notes

nb: 'orbit' never used. program just prints 'orb' (but must be same format as
original PRN_GPS file).

There is also an optional input file, 'exceptions.in' where we may list any
additional clock assignments that we believe are incorrect in the OAs.
The program will over-ride the OA assignments with those from 'exceptions.in'.
This file uses same format as above.


### Rough description of method

Downloads all the OA (operational advisory) files from:
 * https://www.navcen.uscg.gov/?Do=gpsArchives

There is one OA file for each day.

Download path (DD=day of year (1-366); YYYY=year):
 * https://www.navcen.uscg.gov/?Do=getAdvisory&advisory=DD&year=YYYY

Forms an output file, named allClockSwapsByDay.out, that contains one line
for each day that a clock assignment was swapped.
The reason for creating the output file is so we don't have to read through 
every single OA file each time. 
When you run the program, it first checks this output file (if it exists), and
just starts where it left off.

Then, this OA output file is read from disk into a list.

Also, the program downloads the PRN_GPS file from JPL/NASA, and reads it into a
list.

Combines the OA list with the PRN_GPS list to make a new list, called 
PRN_GPS_GPSDM, which has correct PRN-SVN-Clock mappings.

Then, reads in the optional exceptions.in file.
Overwrites any assignements with those given.


********************************************************************************

*There are a few instances where this is not the case.
There are some days for which data was being recorded in the JPL files, but the
OAs say no clock was in use.
Also, there are a couple of days where OA says a Rb clock was being used, but I
think it was actually a Cs clock.

e.g., SVN 40 is marked 'CB' for a few days in 2011, I think it's Cs. 
Also, there are a few assignments that I think are incorrect. This assumption is
based on two facts, 1) that there is no gap in the clock data when the OAs says
the clock was swapped (which is impossible), and the Allan Variance, histogram
etc. (calculated by me) indicates this should be a Cs clock (OA has Rb). The
lines in question are:

  * 2005-12-01   2005-12-18   39   09   IIA   A-1   Cs   !!!OA has rb (*1)
  * 2005-12-21   2007-10-29   39   09   IIA   A-1   Cs   !!!OA has rb (*2)




















