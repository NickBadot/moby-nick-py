"""
@file esrgrid.py
@author Nick
System to send an emergency vehicle into a SUMO simulation and make changes to driving policies and object behavious on the emergency vehicle's route. 
Changes are applied based on an emergency response plan decided by the gravity of the emergency and a fuzzy logic system that evaluates congestion based on
average vehicle speed and occupancy level.
"""
import os, sys, subprocess, random, math

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools"))
    sys.path.append(
        os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools"))
    from sumolib import checkBinary
except ImportError:
    sys.exit(
        "please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")
import traci, sumolib

# import fuzzy logic libraries and FCL file
import fuzzy.storage.fcl.Reader

system = fuzzy.storage.fcl.Reader.Reader().load_from_file("congestion_fcl.fcl")

PORT = 8876
map = sumolib.net.readNet("grid10.net.xml")


# EMERGENCY VEHICLE DISPATCH AND ROUTING FUNCTIONS
# choose an emergency response plan based on occupancy level and average speed on a vehicles route
def chooseERP(route, el):
    cl = getCongestionLevel(route)
    # if else statements based on el/cl -> erp mappings
    print
    "el = ", el, " cl = ", cl
    if (cl + el) > 7:
        return 5
    elif (cl >= 4 & el == 1) | (cl == 4 & el == 2):
        return 4
    elif (el == 3) & (cl < 4):
        return 3
    elif (el == 2) & (cl < 4) & (cl > 1):
        return 2
    else:
        return 1


# get the congestion level on a given route
def getCongestionLevel(route):
    ol = 0  # occupancy
    avs = 0  # average vehice speed
    count = 0
    for edge in route:
        ol += traci.edge.getLastStepOccupancy(edge)
        for lane in getLanes(edge):
            count += 1
            avs += traci.lane.getLastStepMeanSpeed(lane)
    ol = ol / (len(route) - 1)
    avs = avs / count
    print
    "OL = ", ol, "  AVS = ", avs
    cv = fuzzy(ol, avs)
    if cv <= 10:
        return 1
    elif cv <= 25:
        return 2
    elif cv <= 50:
        return 3
    elif cv <= 70:
        return 4
    else:
        return 5


# fuzifes occupancy level and average vehicle speed and defuzzifies congestion level
def fuzzy(ol, avs):
    my_input = {
        "Occupancy_Level": 0.0,
        "Avg_Traffic_Speed": 0.0
    }
    my_output = {
        "Congestion_Value": 0.0
    }
    # set input values
    my_input["Occupancy_Level"] = ol
    my_input["Avg_Traffic_Speed"] = avs
    system.calculate(my_input, my_output)
    j = my_output["Congestion_Value"]
    # print str(j)
    return j


# sends an emergency vehicle along a fixed route taken from the route of a vehicle in the vehicles array
def sendEmergencyVehicleFixed(vehicles):
    route = traci.vehicle.getRouteID(vehicles[4])
    traci.vehicle.add(vehID="0a", routeID=route, typeID="emergency")
    print
    "Ambulance route is: \n", traci.vehicle.getRoute("0a"), "  ERP : ", chooseERP(traci.vehicle.getRoute("0a"), 3)
    erp = chooseERP(traci.vehicle.getRoute("0a"), 3)
    if erp > 3:
        reroute(traci.vehicle.getRoute("0a"), "0a")
    return ("0a", erp)


# reroutes vehicles on the ambulance route by setting the travel time oof edges to -1 and running the rerouting algorithm
def reroute(route, ambulanceID):
    for edge in route:
        traci.edge.adaptTraveltime(edge, 1000000)
    for edge in route:
        vehicles = traci.edge.getLastStepVehicleIDs(edge)
        for v in vehicles:
            if v is not ambulanceID:
                traci.vehicle.rerouteTraveltime(v)


# returns next edge in a route given route and current edge
def getNextEdge(v):
    route = traci.vehicle.getRoute(v)
    edge = traci.vehicle.getRoadID(v)
    i = 0
    if edge != route[-1]:
        for e in route:
            if (e == edge):
                return route[i + 1]
            i += 1


# gets arrival time at next junction
def getArrivalTimeAtNextJunction(vehID):
    lane = traci.vehicle.getLaneID(vehID)
    len = traci.lane.getLength(lane)
    speed = traci.vehicle.getSpeed(vehID)
    traversed = traci.vehicle.getLanePosition(vehID)
    distance = len - traversed
    if speed != 0:
        time = distance / speed
    else:
        time = 50  # if ambulance is stationary pick an arbitrary time
    print
    "estimated time: ", time
    return time


# TRAFFIC LIGHT FUNCTIONS
# return next traffic light given current and next edge as well as the index of the connection used to go from edge1 to edge2
def getNextLight(edge1, edge2):
    if edge1:
        if edge2:
            lights = traci.trafficlights.getIDList()
            for tl in lights:
                tlinks = traci.trafficlights.getControlledLinks(tl)
                i = -1
                for link in tlinks:
                    i += 1
                    for edgelink in link:
                        if (edge1 in edgelink[0]) & (edge2 in edgelink[1]):
                            return (tl, i)


# Sets next light green or extends phase duration as needed		
def setNextLight(edge1, edge2, time):
    tlInfo = getNextLight(edge1, edge2)
    if tlInfo:
        i = tlInfo[1]
        tlid = tlInfo[0]
        print
        "Next light is : ", tlid, " link index ", i
        ryg = traci.trafficlights.getRedYellowGreenState(tlid)
        ryg = list(ryg)
        # if green light extend phase duration
        if (ryg[i] == 'g') | (ryg[i] == 'G'):
            t = traci.trafficlights.getNextSwitch(tlid)
            print
            t
            if not traci.trafficlights.getNextSwitch(tlid) / 1000 > time:
                print
                "duration extended :", tlid
                traci.trafficlights.setPhaseDuration(tlid, traci.trafficlights.getPhaseDuration(tlid) + time)
        else:
            found = False
            x = 0
            while not found:
                traci.trafficlights.setPhase(tlid, x)
                x += 1
                ryg = traci.trafficlights.getRedYellowGreenState(tlid)
                ryg = list(ryg)
                if (ryg[i] == 'g') | (ryg[i] == 'G'):
                    found = True
                    print
                    str(ryg)
                    if not traci.trafficlights.getNextSwitch(tlid) / 1000 > time:
                        traci.trafficlights.setPhaseDuration(tlid, traci.trafficlights.getPhaseDuration(tlid) + time)


# reset light safter Emergency vehicle passes them
def revertLight(edge1, edge2):
    tlid = getNextLight(edge1, edge2)
    if (tlid):
        traci.trafficlights.setProgram(tlid[0], "0")


# SPEED LIMIT FUNCTIONS
def alterSpeedLimit(edgeID, val):
    if not (edgeID == ""):
        print
        getLanes(edgeID)
        for lane in getLanes(edgeID):
            speedLimit = traci.lane.getMaxSpeed(lane)
            traci.lane.setMaxSpeed(lane, speedLimit + val)
    # print "speed limit changed : ",lane


# LANE CLEARANCE FUNCTIONS & PERMISSION CHANGE FUNCTIONS
# get a list of lanes belonging to an edge
def getLanes(edgeID):
    lanes = []
    count = sumolib.net.Edge.getLaneNumber(map.getEdge(edgeID))
    for i in range(0, count):
        lane = edgeID + "_" + str(i)
        lanes.append(lane)
    return lanes


# set permissions for single lane
def setLanePermission(laneID, list):
    allowed = traci.lane.getAllowed(laneID)
    if not (allowed == list):
        traci.lane.setAllowed(laneID, list)
    return allowed


# set new permissions on all lanes of an edge
def setNewEdgeLanePermissions(edgeID):
    permissions = []
    for lane in getLanes(edgeID):
        permissions.append(setLanePermission(lane, []))
    print
    "permission changed :", permissions
    return permissions


# revert old permissions after an ambulance leaves an edge
def revertLanePermissions(edgeID, permissions):
    if edgeID is "":
        return 0
    i = 0
    for lane in getLanes(edgeID):
        if not i >= len(permissions):
            setLanePermission(lane, permissions[i])
            i += 1
            print
            " reverted permissions :", lane


# clears a lane
def clearLane(laneID, ambulanceID):
    vehicles = traci.lane.getLastStepVehicleIDs(laneID)
    for v in vehicles:
        if not (v == ambulanceID):
            changeLane(v)
            print
            "vehicle moved:", v


# if lanes are available vehicles moved to another random lane for 20s
def changeLane(vehID):
    edge = traci.vehicle.getRoadID(vehID)
    lanes = getLanes(edge)
    print
    str(lanes)
    if len(lanes) > 1:
        i = random.randint(0, len(lanes) - 1)
        if (lanes[i] == traci.vehicle.getLaneID(vehID)):
            traci.vehicle.changeLane(vehID, i, 30)
            print
            "vehicle moved ", vehID
        else:
            if i - 1 >= 0:
                traci.vehicle.changeLane(vehID, i - 1, 30)
                print
                "vehicle moved ", vehID
            else:
                traci.vehicle.changeLane(vehID, i + 1, 30)
                print
                "vehicle moved ", vehID


# Implement changes to driving policy based on ERP
def changeDrivingPolicies(ambulanceID, ambulanceEdge, previousEdge, lanePermissions, erp):
    if erp > 1:  # change spped limit
        alterSpeedLimit(previousEdge, -10)
        alterSpeedLimit(ambulanceEdge, 10)
    # if erp
    # change and revert lane ppermissions
    if (erp == 3) | (erp == 5):
        revertLanePermissions(previousEdge, lanePermissions)
        lanePermissions = setNewEdgeLanePermissions(ambulanceEdge)
    # clear lanes
    if erp > 2:
        clearLane(traci.vehicle.getLaneID(ambulanceID), ambulanceID)
    return lanePermissions


def run(ambulanceID, erp):
    step = 0
    traci.init(PORT)
    ambulanceEdge = ""
    permissions = []
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        vehicles = traci.vehicle.getIDList()
        if step is 20:
            emergencyInfo = sendEmergencyVehicleFixed(vehicles)
            ambulanceID = emergencyInfo[0]
            erp = emergencyInfo[1]
            dispatchTime = step
        if (ambulanceID in traci.simulation.getArrivedIDList()):
            print
            "Ambulance has left after", str(step - dispatchTime), " seconds. "
        if ambulanceID in vehicles:
            if (traci.vehicle.getRoadID(ambulanceID) != ambulanceEdge) & (
                    traci.vehicle.getRoadID(ambulanceID) in traci.vehicle.getRoute(ambulanceID)):
                prevEdge = ambulanceEdge
                ambulanceEdge = traci.vehicle.getRoadID(ambulanceID)
                permissions = changeDrivingPolicies(ambulanceID, ambulanceEdge, prevEdge, permissions, erp)
                setNextLight(ambulanceEdge, getNextEdge(ambulanceID), getArrivalTimeAtNextJunction(ambulanceID))
                revertLight(prevEdge, ambulanceEdge)
        step += 1
    traci.close()


if __name__ == "__main__":
    sumoBinary = checkBinary('sumo-gui')
    sumoProcess = subprocess.Popen(
        [sumoBinary, "-c", "gridcfg.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)],
        stdout=sys.stdout, stderr=sys.stderr)
    run("", -1)
# sumoProcess.wait()
