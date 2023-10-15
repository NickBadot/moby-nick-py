"""
@file esrnyc.py
@author Nick
System to send an emergency vehicle into a SUMO simulation and make changes to driving policies and object behavious on the emergency vehicle's route. 
Changes are applied based on an emergency response plan decided by the gravity of the emergency and a fuzzy logic system that evaluates congestion based on
average vehicle speed and occupancy level.
"""
import os,sys, subprocess, random, math
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools")) 
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools")) 
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")
import traci,sumolib


#import fuzzy logic libraries and FCL file
import fuzzy.storage.fcl.Reader
system = fuzzy.storage.fcl.Reader.Reader().load_from_file("congestion_fcl.fcl")

PORT = 8876
map=sumolib.net.readNet("nycmap2.net.xml")

#FUZZY LOGIC ERP CHOOSING SYSTEM
#choose an emergency response plan based on occupancy level and average speed on a vehicles route
def chooseERP (route, el) :
	cl = getCongestionLevel(route)
	# if else statements based on el/cl -> erp mappings
	print "el = ", el, " cl = ",cl
	if (cl+el) > 7:
		return 5
	elif (cl>=4 & el == 1) | (cl==4 & el==2):
		return 4
	elif (el==3) & (cl < 4) :
		return 3
	elif (el==2) & (cl < 4) & (cl > 1):
		return 2
	else:
		return 1

#get the congestion level on a given route based on average vehicle speed and occupancy level
def getCongestionLevel (route) :
	ol=0 	#occupancy levell
	avs=0	#average vehice speed
	count=0
	for edge in route:
		ol+=traci.edge.getLastStepOccupancy(edge)
		for lane in getLanes(edge):
			count+=1
			avs+=traci.lane.getLastStepMeanSpeed(lane)
	ol = ol/(len(route)-1)
	avs=3.6*(avs/count) #1 m/s = 3.6 km/h
	print "OL = ",ol,"  AVS = ",avs 
	cv=fuzzy(ol,avs)
	if cv <= 10 :
		return 1
	elif cv <= 25 :
		return 2
	elif cv <= 50:
		return 3
	elif cv <= 70 :
		return 4
	else :
		return 5
	
#fuzifes occupancy level and average vehicle speed and defuzzifies congestion level	
def fuzzy (ol,avs) :
	my_input = {
		"Occupancy_Level" : 0.0,
		"Avg_Traffic_Speed" : 0.0
		}
	my_output = {
		"Congestion_Value" : 0.0
		}
	my_input["Occupancy_Level"] = ol # set input values to the ol and avs values passed into the functon
	my_input["Avg_Traffic_Speed"] = avs
	system.calculate(my_input, my_output)
	j = my_output["Congestion_Value"]
	#print str(j)
	return j
	
#EMERGENCY VEHICLE DISPATCH, REROUTING AND MONITORING functions
# sends an emergency vehicle along a fixed route taken from the route of a vehicle in the vehicles array	
def sendEmergencyVehicleFixed (vehicles) :
	route = traci.vehicle.getRouteID(vehicles[4])
	traci.vehicle.add(vehID="0a", routeID=route , typeID="emergency")
	erp=chooseERP(traci.vehicle.getRoute("0a"), 3)
	if erp >= 3 :
		reroute (traci.vehicle.getRoute("0a"), "0a")
	return ("0a",erp)

#reroutes vehicles on the ambulance route by setting the adated travel time of edges to a large number and running the rerouting algorithm	
def reroute (route, ambulanceID):
	for edge in route :
		traci.edge.adaptTraveltime(edge,10000000)
	for edge in route :
		vehicles = traci.edge.getLastStepVehicleIDs(edge)
		for v in vehicles:
			if v is not ambulanceID:
				traci.vehicle.rerouteTraveltime(v, currentTravelTimes=False)
				#print "Vehicle route : ",traci.vehicle.getRoute(v)
					
#returns next edge in a vehicles route by checking the currrent edge against the edges in the route			
def getNextEdge(v) :
	route = traci.vehicle.getRoute(v)
	edge = traci.vehicle.getRoadID(v)
	i=0
	if edge != route[-1]:
		for e in route:
			if (e==edge):
				return route[i+1]
			i+=1
		
#gets arrival time at next junction		
def getArrivalTimeAtNextJunction (vehID) :
	lane = traci.vehicle.getLaneID(vehID)
	len = traci.lane.getLength(lane)
	speed = traci.vehicle.getSpeed(vehID)
	traversed = traci.vehicle.getLanePosition(vehID) 
	distance = len-traversed  #subtract the length travelled along the edge by the tota length to find the distance left to go
	if speed != 0:	
		time = distance/speed
	else :
		time=50		#if ambulance is stationary (i.e. when it first enters the simulation)  pick an arbitrary time
	return time+5
	
#TRAFFIC LIGHT FUNCTIONS
#return information about the next traffic light (id and link index) given current and next edge 
def getNextLight(edge1, edge2) :
		if edge1 :
			if edge2 :
				lights= traci.trafficlights.getIDList()
				for tl in lights:
					tlinks= traci.trafficlights.getControlledLinks(tl) 
					i=-1
					for link in tlinks:
						i+=1					#increment to get the link index of the desired connection
						for edgelink in link : 
							if ( edge1 in edgelink[0] ) & (edge2 in edgelink[1]):
								return (tl,i)
							
# Sets next light green or extends phase duration as needed
def setNextLight(edge1, edge2, time) :
	tlInfo = getNextLight(edge1,edge2)
	if tlInfo:
		i = tlInfo[1]
		tlid = tlInfo[0]
		duration = traci.trafficlights.getPhaseDuration(tlid)
		ryg = list(traci.trafficlights.getRedYellowGreenState(tlid))
		if (ryg[i]=='G') :
			if not traci.trafficlights.getNextSwitch(tlid)/10000 > time:  #if the light is already green we just want to extend the phase duration
				traci.trafficlights.setPhaseDuration(tlid, traci.trafficlights.getPhaseDuration(tlid)/1000 +time)
		else :
			found = False
			x=0
			while not found :		#if the light is not green we loop through the phases of the traffic light until one is found giving the emergency vehicle priority
				traci.trafficlights.setPhase(tlid, x)
				x+=1
				ryg = traci.trafficlights.getRedYellowGreenState(tlid)
				ryg=list(ryg)
				if (ryg[i]=='G') :
					found = True
					if not traci.trafficlights.getNextSwitch(tlid)/10000 > time:
						traci.trafficlights.setPhaseDuration(tlid ,traci.trafficlights.getPhaseDuration(tlid)/1000 +time)
		return duration
	return 0
				
#reset light safter Emergency vehicle passes them		
def revertLight (edge1 , edge2, phaseDuration) :
	tlid = getNextLight(edge1,edge2)
	if (tlid) :
		traci.trafficlights.setProgram(tlid[0], "0")
		if phaseDuration != 0 :
			traci.trafficlights.setPhaseDuration(tlid[0] , phaseDuration/1000)
		
#SPEED LIMIT FUNCTIONS
def alterSpeedLimit(edgeID, val) :
	if not (edgeID == ""):
		for lane in getLanes(edgeID):
			speedLimit = traci.lane.getMaxSpeed(lane)
			traci.lane.setMaxSpeed(lane, speedLimit+val)
			
#LANE CLEARANCE FUNCTIONS & PERMISSION CHANGE FUNCTIONS
#get a list of lanes belonging to an edge by getting the number of lanes and appending lane indices to the edge ID
def getLanes(edgeID):
	lanes=[]
	count = sumolib.net.Edge.getLaneNumber(map.getEdge(edgeID))
	for i in range(0,count) :
		lane = edgeID+"_"+str(i)
		lanes.append(lane)
	return lanes
	
#set the permissions of all lanes in an edge	
def setPermissions (edgeID, perm):
	if edgeID == "" :	# if edge does not exist (occurs at the very start)
		return []
	permissions=[]
	i=0
	for lane in getLanes(edgeID) :	
		allowed=traci.lane.getAllowed(lane)
		permissions.append(allowed)
		if len(perm) > i :	#if we are reverting a previously altered lane then the perm variable will contain permission sets
			if not (allowed == perm[i]):	#this check avoids the "disappearing edge" bug
				traci.lane.setAllowed(lane,perm[i])	
		else :				#if it is not a previously altered edge the perm variable will be empty and we set the lae to accept any vehicle bby passing an empty list
			if not (allowed == [] ):	
				traci.lane.setAllowed(lane,[])
		i+=1
		#print traci.lane.getAllowed(lane)
	return permissions

#clears a lane	by caling the changelane method on each vehicle
def clearLane(laneID,ambulanceID):
	vehicles = traci.lane.getLastStepVehicleIDs(laneID)
	for v in vehicles :
		if not (v == ambulanceID) :
			changeLane(v)
	
#if lanes are available vehicles moved to another random lane for 20s
def changeLane(vehID):
	edge = traci.vehicle.getRoadID(vehID)
	lanes = getLanes(edge)
	if len(lanes)>1 :
		i = random.randint(0,len(lanes)-1)
		if not (lanes[i] == traci.vehicle.getLaneID(vehID)) :
			traci.vehicle.changeLane(vehID, i, 1)
			print "vehicle moved ",vehID
		else :
			if i-1 >= 0 :
				traci.vehicle.changeLane(vehID, i-1, 1)
				print "vehicle moved ",vehID
			else :
				traci.vehicle.changeLane(vehID, i+1, 1)
				print "vehicle moved ",vehID

#Implement changes to driving policy based on ERP
def changeDrivingPolicies(ambulanceID,ambulanceEdge, previousEdge, lanePermissions, erp) :
		if erp > 1 : #change speed limit
			alterSpeedLimit(previousEdge, -10)
			alterSpeedLimit(ambulanceEdge, 10)
		if (erp ==3) | (erp==5) :	 #change and revert lane permissions
			setPermissions(previousEdge,lanePermissions)
			lanePermissions = setPermissions(ambulanceEdge,[])
		if erp > 2 : #clear lanes
			clearLane(traci.vehicle.getLaneID(ambulanceID), ambulanceID)
		return lanePermissions
	
#main execution loop of the system	
def run(ambulanceID, erp) :
	step=0
	traci.init(PORT)
	ambulanceEdge=""	
	phaseDuration=0
	permissions = []			#keep an array of lane permissions to revert the permissions of lanes that have been changed
	while traci.simulation.getMinExpectedNumber() > 0:
		traci.simulationStep()
		vehicles=traci.vehicle.getIDList()
		if  step is 20 :
			emergencyInfo= sendEmergencyVehicleFixed(vehicles)
			ambulanceID=emergencyInfo[0]
			erp = emergencyInfo[1]
			dispatchTime=step
		if (ambulanceID in traci.simulation.getArrivedIDList()):
			print "Ambulance has left after" , str(step-dispatchTime) , " seconds. "
		if ambulanceID in vehicles :
			if(traci.vehicle.getRoadID(ambulanceID) != ambulanceEdge) & (traci.vehicle.getRoadID(ambulanceID) in traci.vehicle.getRoute(ambulanceID)): #detect if ambulance has reached new edge
				prevEdge = ambulanceEdge
				ambulanceEdge = traci.vehicle.getRoadID(ambulanceID)
				permissions=changeDrivingPolicies(ambulanceID,ambulanceEdge, prevEdge, permissions,erp)
				revertLight(prevEdge , ambulanceEdge, phaseDuration)
				#phaseDuration=setNextLight(ambulanceEdge, getNextEdge(ambulanceID),getArrivalTimeAtNextJunction(ambulanceID))

		step += 1
	traci.close()			
	
if __name__ == "__main__":
	sumoBinary = checkBinary('sumo-gui')
	sumoProcess = subprocess.Popen([sumoBinary, "-c", "nyc3.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
	run("",-1)
	#sumoProcess.wait()
