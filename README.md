# Update PRN_SVN using NASA/JPL operational advisories


Each operational GPS satellite has a PRN (PseudoRandom Noise code).
This is a label 1-32.
On any given day, one one sattelite have each PRN, however, the PRN assigned
to any specific satellite may change several times over the life of the 
satellite.
Each indevidual sattelite also has a unique identifier, called an SVN (Space
Vehicle Number), which never changes.
Also, each sattelite may have a Rb and a Cs clock, only one of which is 
transmitting at any given time.

The JPL bias data files list the data labelled by PRN (not SVN). They also don't
state which clock type (Rb/Cs) was in use.
To perform any analysis, however, we need to know which indevidual satellite
we are looking at, and what type of clock it is using.

JPL supplies a file, PRN_GPS, that maps each PRN to the SVN for a given day.
Available:
ftp://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz
This file also ostensibly states which clock (Rb or Cs) was in use that day.
The PRN-SVN mappings are accurate, however, the clock mappings are known to be
largely wrong.

The US Navigation Center makes available so-called operational advisory
(GPS OPSADVISORIES) files. There is one such file for every single day.
These files state which clock was being used by each PRN on that day, but do
not state which SVN the satellite is.
For the most part, these files accurately record the clock-PRN mappings.*

This program reads both the JPL PRN_GPS file, to determine the PRN-SVN mappings,
and the USNavCen operational advisory files, to determine the PRN-clock mappings.
It combines these two lists to form a new list that has the full correct
PRN-SVN-Clock mappings. It outputs this list in a new file, called
PRN_GPS_GPSDM, that is in roughly the same format as the original PRN_GPS file.

(Or, at least, it _will_ do this, once the code is finished..)


### Rough description of method

**Note** the code is far from finished, still in the testing phase.

Downloads all the OA (operational advisory) files from:
https://www.navcen.uscg.gov/?Do=gpsArchives
There is one OA file for each day.

Download path:
https://www.navcen.uscg.gov/?Do=getAdvisory&advisory=DD&year=YYYY
-DD=day of year (1-366), YYYY=year

Forms an output file, named allClockSwapsByDay.out, that contains one line
for each day that a clock assignment was swapped.
The reason for creating the output file is so we don't have to read through 
every single OA file each time. 
When you run the program, it first checks this output file (if it exists), and
just starts where it left off.

Then, this output file is read from disk into a list.

Also, the program downloads the PRN_GPS file from JPL/NASA, and reads it into a
list.





*There are a few instances where this is not the case.
There are some days for which data was being recorded in the JPL files, but the
OAs say no clock was in use.
Also, there are a couple of days where OA says a Rb clock was being used, but I
think it was actually a Cs clock.
