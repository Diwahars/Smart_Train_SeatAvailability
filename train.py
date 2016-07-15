
# author: Ashish_G

import urllib2
import sys
try:
	import station_codes as sd
except:
	print("station_codes.py is missing! Please place it in the same directory")
	sys.exit(1)
import json
import urllib
try:
	from bs4 import BeautifulSoup as bsp
except:
	print("BeautifulSoup not found")
	print("Install it by: 'pip install bs4'")
	sys.exit(1)



api_keys=["yagmk5963","bwlbe8046"]



def cfn(x):
    return {
        'SL':"SLEEPER CLASS",
        '3A':"THIRD AC",
        '2A':"SECOND AC",
        '1A':"FIRST AC"
    }[x]

def getStnName(st_code):
	st_code=st_code.upper()
	for stn in sd.sdict:
		pill=stn.split("-")
		if pill[1].strip()==st_code:
			return pill[0]
	return False

def getTrainName(t_code):
	for stn in sd.tdict:
		if t_code==stn[:5]:
			return stn[5:].strip()

	return False

def getFare(sfrom,sto,trnno,tclass,date):
	furl="http://railwayapi.com/getFareEnquiry.php"

	sfrom=sfrom.upper()
	sto=sto.upper()
	date="-".join(date.split('/')[::-1])
	nfrom=getStnName(sfrom)
	nto=getStnName(sto)
	sfrom="+".join((nfrom+" - "+sfrom).split(" "))

	sto="+".join((nto+" - "+sto).split(" "))
	tr="+".join((str(trnno)+" "+getTrainName(trnno)).split())
	params="pnrQ="+sfrom+"&dest="+sto+"&train="+tr+"&jdate="+date+"&age=30&jquota=GN"

	#params=urllib.urlencode({'pnrQ':p_from,'dest':p_to,'train':p_tr,'jdate':p_date,'age':30,'jquota':'GN'})
	#print(params)
	e=urllib2.Request(furl,data=params)
	c=urllib2.urlopen(e).read()
	sp=bsp(c,"lxml")
	trA=sp.findAll("tr")

	tclass=cfn(tclass)
	for i,tr1 in enumerate(trA):
		if i==0:
			continue
		if str(tr1.findAll('td')[5].text)==tclass:
			return tr1.findAll('td')[4].text
	return False

def stncodewithname(st_code):
	pass


def status(sfrom,to,trno,date,sclass,quota):
	d=date.split('/')
	date=d[1]+"/"+d[0]+"/"+d[2]
	sfrom=str(sfrom).upper()
	to=str(to).upper()
	sclass=str(sclass).upper()
	quota=str(quota).upper()
	purl="http://railwayapi.com/getSetAvailability.php"
 	#params="pnrQ=SDL&dest=BPL&train=18234&jdate=07%2F15%2F2016&jclass=3A&jquota=GN"
 	params=urllib.urlencode({'pnrQ':sfrom,'dest':to,'train':trno,'jdate':date,'jclass':sclass,'jquota':quota})
 	#print(params)
 	c=urllib2.Request(purl,data=params)
	d=urllib2.urlopen(c).read()
	#print(d)
	#open("save.txt","w").write(d).close()
	soup=bsp(d,"lxml")
	if len(soup.findAll('tr'))<6:
		return False
	return soup.findAll('tr')[1].findAll('td')[7].text

def generate_route_link(train_number,api_key):
	return "http://api.railwayapi.com/route/train/"+str(train_number)+"/apikey/"+api_key+"/"

def mainfun():
	print("*****************************************")
	print("*******\tSmart Seat Availability\t ********")
	train_number=raw_input("# Enter train number: ")
	print("->>>> Train: "+getTrainName(train_number))
	from_s=raw_input("# Enter from station code: ").upper()
	to_s=raw_input("# Enter destination station code: ").upper()
	jr_date=raw_input("# Enter travel date (DD/MM/YYYY): ")
	jr_class=raw_input("# Class (SL/3A/2A/1A): ").upper()



	for i,key in enumerate(api_keys):
		try:
			route_link=generate_route_link(train_number,key)
			json1=json.load(urllib2.urlopen(route_link))
			route=json1['route']
			break
		except:
			if i<len(api_keys)-1:
				print("Key Verification failed! Trying another key")
			else:
				print("All attempts failed! Exiting...")
				sys.exit(1)
	bstn=[]
	for station in route:
		if(station['code']==from_s):
			break
		bstn.append(station['code'])
	bstn=bstn[::-1]
	#print("Stations: "+str(bstn))
	print("Route Fetch complete:"+str(len(bstn)))


	initial_fare=getFare(from_s,to_s,train_number,jr_class,jr_date)
	found=False
	print("Connecting to Server...")
	av=status(from_s,to_s,train_number,jr_date,jr_class,"GN")
	if av==False:
		print("Something went wrong!")
		sys.exit(1)
	if av.startswith("AVAILABLE"):
		print("Seat available from "+from_s+": "+av+". Fare: Rs."+initial_fare)
		found=True

	if not found:
		print("Unavailable from provided source. Searching for stations!")
		print("*********************************************************")
		check_pos=int(len(bstn)/2)
		try_stn=bstn[check_pos]
		lastfound=False
		start=0
		done=False
		end=len(bstn)-1
		while True:
			if done:
				break
			if start==(end-1):
				done=True
				start=end
			av=status(try_stn,to_s,train_number,jr_date,jr_class,"GN")
			if av.startswith("AVAILABLE"):
				lastfound=try_stn
				print("Available from "+try_stn+": "+av)
				end=check_pos
			else:
				start=check_pos
			check_pos=(start+end)/2
			try_stn=bstn[check_pos]
			continue
		if lastfound==False:
			print("Please try another date. No seats are available")
		else:
			fare=getFare(lastfound,to_s,train_number,jr_class,jr_date)
			diff=int(fare)-int(initial_fare)
			print("\n********************************************************")
			print("\n********************************************************")
			print("BEST SHOT: "+getStnName(lastfound)+"("+lastfound+")-"+getStnName(to_s)+"("+to_s+")")
			print("Total Fare: Rs."+fare+" ( Rs."+ str(diff) +"  greater than provided source)")
			print("\n********************************************************")
			print("\n********************************************************")
			print(" * - * - - * - - - * - - - - i2o.in - - - - * - - - * - - * - *")
	#print(generate_seatav_link("18234","SDL","BPL","25-07-2016","SL"))
if __name__ == '__main__':
	mainfun()
