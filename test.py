import urllib.request


url = 'https://www.navcen.uscg.gov/?Do=getAdvisory&advisory=37&year=2012'
response = urllib.request.urlopen(url)
data=response.read()
text = data.decode('utf-8')
#print(data)
#print(text)

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


prn_index_list=findall(text,"PRNS")
clk_index_list=findall(text,"CLOCK ")

#
str_prn_list=""
for i in prn_index_list:
  end=text.find("\n",i)
  temp=text[i+4:end+1]
  temp=temp.replace(" ", "")
  temp=temp.replace("\r", "")
  temp=temp.replace("\n", "")
  str_prn_list=str_prn_list+temp+","
  
str_prn_list = str_prn_list[:-1]

prn_list = [int(e) if e.isdigit() else e for e in str_prn_list.split(',')]

str_clk_list=""
for i in clk_index_list:
  beg=text.find(":",i)
  end=text.find("\n",beg)
  temp=text[beg+1:end+1]
  temp=temp.replace(" ", "")
  temp=temp.replace("\r", "") #kills the carrige return/newlines
  temp=temp.replace("\n", "")
  temp=temp.replace("RB", "Rb")
  temp=temp.replace("CS", "Cs")
  str_clk_list=str_clk_list+temp+","

str_clk_list = str_clk_list[:-1]

clk_list = [e for e in str_clk_list.split(',')]



print(prn_list)
print(clk_list)









