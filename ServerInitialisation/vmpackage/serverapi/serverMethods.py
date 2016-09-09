import logging
import requests
import json
import time

logging.getLogger("requests").setLevel(logging.WARNING)
isVerbose = False

WAIT_TIME = 30 #seconds 
MAX_NO_ATTEMPTS = 5

""" This method is almost identical to the rest_submit_postrequest found in serverCreationInitialisation.py, except it does not capture
   a serverUUID """
def rest_submit_postrequest(theURL, payload, headers, auth_parms):
    retry = True
    count = 1
    
    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):
        res = requests.post(theURL, payload, auth=(auth_parms['token'], ''), headers=headers)   
        print("==============================================================")
        print "Request submitted, response URL and contents:"
        print(res.url)
        print res.content
        print("HTTP response code: ", res.status_code)

        # Status 202 (Accepted) is good
        if ((res.status_code == 202) or (res.status_code == 200)):
            response = json.loads(res.content)
            retry = False
            return response
        
        if (res.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count 
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            # Something else went wrong. Pick out the status code and message
            response = json.loads(res.content)
            retry = False
            return ""
        print("==============================================================")       
    
    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        print "HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server"
        #print(response['message'] + " (error code: " + response['errorCode'] + ")")
    
    return ""

#This method is used to send a REST PUT request to the server
def rest_submit_putrequest(theURL, payload, headers, auth_parms):
    
    retry = True
    count = 1
    
    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):
        
        res = requests.put(theURL, payload, auth=(auth_parms['token'], ''), headers=headers)   
        #    print(res.content)
        print("==============================================================")
        print(res.url)
        print("res=" + str(res))
        print res.content
        print("HTTP response code: ", res.status_code)
        
        # Status 202 (Accepted) is good
        if ((res.status_code == 202) or (res.status_code == 200)):
            response = json.loads(res.content)
            retry = False
            return response
        
        if (res.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count 
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            # Something else went wrong. Pick out the status code and message
            response = json.loads(res.content)
            retry = False
            return "" 
        print("==============================================================")      
    
    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        print "HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server"
        #print(response['message'] + " (error code: " + response['errorCode'] + ")")
    
    return ""

#This method is used to get the details of a specified image
def list_image(auth_params, uuid):
    """ Get Image details """

    # Setup serach filter
    sf = { "searchFilter" :
          { "filterConditions": [{"condition": "IS_EQUAL_TO",
                                  "field": "resourceUUID",
                                  "value": [uuid]
                                 }
                                ]
          }
        }

    if (isVerbose):
        print("sf=")
        print sf
        print("---")

    result_set = rest_list_resource(auth_params, "image", sf)

    if result_set['totalCount'] == 0:
        raise RuntimeError("Image " + uuid + " not found or you do not have permissions to use it")

    print("==== Image Result ====")
    print result_set
    print("=========");
    # return just the first element (there was only one, right ?), otheriwse we end up doing e.g. img_ret['list'][0]['vdcUUID']
    # all over the place
    return result_set['list'][0]

#Use a REST request to list the details of a particular resource
def rest_list_resource(auth_parms, res_type, payload):
    print auth_parms
    theURL = auth_parms['endpoint'] + "rest/user/current/resources/" + res_type + "/list"
    print theURL

    if payload != None:
        payload_as_string = json.JSONEncoder().encode(payload);
        print("payload_as_string=" + payload_as_string)
    # Note we use data= and not params= here
    # See: http://requests.readthedocs.org/en/v1.0.1/user/quickstart/
    #
    # Also, we need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    print("theURL=" + theURL)
    
    retry = True
    count = 1

    #Retry the request a specified number of times if the request fails
    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):
        
        if payload != None:
            res = requests.get(theURL, data=payload_as_string, auth=(auth_parms['token'], ''), headers=headers)
        else:
            res = requests.get(theURL, auth=(auth_parms['token'], ''), headers=headers)

        print("==============================================================")
        print(res.url)
        print("res=" + str(res))
        print res.content
        
        # Status 202 (Accepted) is good
        if (res.status_code == 200):
            response = json.loads(res.content)
            retry = False
            return response

        #Server busy
        if (res.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count 
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            # Something else went wrong. Pick out the status code and message
            response = json.loads(res.content)
            print("HTTP response code: ", res.status_code)
            retry = False
            return ""  
    
    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        raise RuntimeError("HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server")

    return ""

#This method uses a REST PUT request to change the status(Start/Stop) of a server
def rest_change_server_status(auth_parms, server_uuid, new_state):
    
    URL = auth_parms['endpoint'] + "rest/user/current/resources/server/" + server_uuid + "/change_status"

    payload = {  "newStatus": new_state,
                "safe" : True
            }

    print(payload)
    payload_as_string = json.JSONEncoder().encode(payload)

    # Need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    result = rest_submit_putrequest(URL, payload_as_string, headers, auth_parms)
    return result

#This method is used to list the details of a resource specified by a UUID
def list_resource_by_uuid(auth_parms, uuid, res_type):
    """ Get details for the specified resource """

    # create search filter for s resource of the specified UUID
    sf = { "searchFilter" :
           { "filterConditions": [{"condition": "IS_EQUAL_TO",
                                   "field": "resourceUUID",
                                   "value": [uuid]
                                  }
                                 ]
           }
        }

    result = rest_list_resource(auth_parms, res_type, payload=sf)

    # Potentially could be a list of resources ?. Just return the lot, the caller can sort out whether it
    # expects one, or multiple
    print result
    return result

#Method used to get the current state of a specified server
def get_server_state(auth_parms, server_uuid):
    # Function to get server state given server uuid
    server_resultset = list_resource_by_uuid(auth_parms, uuid=server_uuid, res_type='SERVER')
    if (server_resultset['totalCount'] != 0):
        server_status = server_resultset['list'][0]['status']
        return server_status
    print 'ERROR: Server not found. UUID: %s' %server_uuid
    return "NOT_FOUND"

#This method is used to "wait" for a resource e.g. a server
def wait_for_resource(auth_parms, res_uuid, state, res_type):
    #check resource has reached desired state
    sf = { "searchFilter" :
           { "filterConditions": [{"condition": "IS_EQUAL_TO",
                                   "field": "resourceUUID",
                                   "value": [res_uuid]
                                  },
                                  {"condition": "IS_EQUAL_TO",
                                   "field": "resourceState",
                                   "value": [state]
                                  }
                                 ]
           }
        }

    res_result = rest_list_resource(auth_parms, res_type=res_type, payload=sf)

    i = 0
    # currently waiting for 100 seconds (up to 10 loops of a 10 second sleep)
    while (res_result['totalCount'] == 0) and (i <= 10):
        print "in wait_for_resource " + state + " loop i = " + str(i) + ", count " + str(res_result['totalCount'])
        i = i + 1
        # wait a while
        time.sleep(10)
        res_result = rest_list_resource(auth_parms, res_type=res_type, payload=sf)

    print("wait_for_resource for uuid " + res_uuid + " state " + state + " returned count of " + str(res_result['totalCount']))
    if res_result['totalCount'] == 1:
        return_val = 0
    else:
        return_val = 1
    return return_val

#Method used to wait for a specific resource, a server
def wait_for_server(auth_parms, server_uuid, state):
    """ Check Server has completed creation """

    print("Begin wait_for_server for server " + server_uuid + " at " + time.strftime("%Y-%m-%d %H:%M:%S"))

    # Similar to wait_for_resource(), except here we look at status, not resourceState
    sf = { "searchFilter" :
           { "filterConditions": [{"condition": "IS_EQUAL_TO",
                                   "field": "resourceUUID",
                                   "value": [server_uuid]
                                  },
                                  {"condition": "IS_EQUAL_TO",
                                   "field": "status",
                                   "value": [state]
                                  }
                                 ]
           }
        }

    server_result = rest_list_resource(auth_parms, res_type="server", payload=sf)

    i = 0
    while (server_result['totalCount'] < 1) and (i <= 24):
        print "in wait_for_server loop i = " + str(i) + ", count " + str(server_result['totalCount'])
        i = i + 1
        # wait a while
        time.sleep(5)
        server_result = rest_list_resource(auth_parms, res_type="server", payload=sf)

    print("wait_for_server(): exit after " + str(i) + " tries")
    print("End wait_for_server for server " + server_uuid + " at " + time.strftime("%Y-%m-%d %H:%M:%S"))
    if server_result['totalCount'] == 1:
        return_val = 0
    else:
        return_val = 1
    return return_val

#Method used to change status of server, and return success once it reaches that state
def change_server_status(auth_parms, server_uuid, state):

    rest_change_server_status(auth_parms, server_uuid, state)

    server_result = wait_for_server(auth_parms, server_uuid, state)
    if server_result == 1:
        print "Problem changing server status, check platform, server uuid: " + server_uuid
    else:
        print "server status changed ok, server uuid: " + server_uuid
    return server_result
