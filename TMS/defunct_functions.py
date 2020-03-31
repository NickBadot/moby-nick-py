# defunct functions

# detects a crash in the simulation
def detectCrash(vehicles, crashedvehicles):
    for v in vehicles:
        if (traci.vehicle.getWaitingTime(v) > 60) & (v not in crashedvehicles):
            return v
    return "none"


# return next traffic light, original version
def getNextLight(edge1, edge2):
    if edge1:
        if edge2:
            lights = traci.trafficlights.getIDList()
            for tl in lights:
                tlinks = traci.trafficlights.getControlledLinks(tl)
                for link in tlinks:
                    for edgelink in link:
                        if (edge1 in edgelink[0]) & (edge2 in edgelink[1]):
                            return tl


# get the indices of all connections between two edges at a given light
def getConnectionIndices(tl, edge1, edge2):
    if edge1:
        if edge2:
            tlinks = traci.trafficlights.getControlledLinks(tl)
            i = -1
            linkies = []
            for link in tlinks:
                i += 1
                for edgelink in link:
                    if (edge1 in edgelink[0]) & (edge2 in edgelink[1]):
                        linkies.append(i)
            return linkies


# sets next light green by changing RYG state, worked on grid but not nyc, caused bugs in SUMO
def setLightGreen(edge1, edge2):
    tlInfo = getNextLight(edge1, edge2)
    if tlInfo:
        i = tlInfo[1]
        tlid = tlInfo[0]
        print
        "Next light is : ", tlid, " link index ", i
        ryg = traci.trafficlights.getRedYellowGreenState(tlid)
        ryg = list(ryg)
        ryg[i] = 'G'
        # print "new : ",ryg," old : ",traci.trafficlights.getRedYellowGreenState(tral)
        traci.trafficlights.setRedYellowGreenState(tlid, str(ryg))


# sends emergency vehicle with id a<ambulancecount> to the location of crashed vehicle v starting with a randomised route
def sendEmergencyVehicle(v, ambulancecount):
    print
    "Crash at :", traci.vehicle.getRoadID(v)
    ambulanceID = "a" + str(ambulancecount)
    routes = traci.route.getIDList()
    route = random.choice(routes)  # choose route at random to enter the ambulance on
    traci.vehicle.add(vehID=ambulanceID, routeID=route, typeID="emergency")
    traci.vehicle.changeTarget(ambulanceID, traci.vehicle.getRoadID(v))  # reroute ambulance to the crashed vehicle
    print
    "Ambulance route is: \n", traci.vehicle.getRoute(ambulanceID)
    return ambulanceID


# used to update ambulance count and print out messages when an ambulance leaves the simulation
def refreshAmbulanceStatus(ambulanceID, step, dispatchTime):
    if (ambulanceID in traci.simulation.getArrivedIDList()):
        responsetime = step - dispatchTime
        print
        "Ambulance has left after", str(responsetime), " seconds. "
        return -1  # return -1 since the result is added to the ambulance count
    else:
        return 0  # if the ambulance doesn't leave ambulance coount does not change


# set new permissions on all lanes of an edge
def setNewEdgeLanePermissions(edgeID):
    permissions = []
    for lane in getLanes(edgeID):
        permissions.append(setLanePermission(lane, []))
    return permissions


# set permissions for single lane
def setLanePermission(laneID, list):
    allowed = traci.lane.getAllowed(laneID)
    if not (allowed == list):
        traci.lane.setAllowed(laneID, list)
    return allowed


# revert old permissions after an ambulance leaves an edge
def revertLanePermissions(edgeID, permissions):
    if edgeID is "":  # make sure a real edge is passed in
        return 0
    i = 0
    for lane in getLanes(edgeID):
        if not i >= len(permissions):
            setLanePermission(lane, permissions[i])
            i += 1
    # print " reverted permissions :",lane
