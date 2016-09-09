import requests
import json
import time
from serverapi.serverMethods import get_server_state
from serverapi.serverMethods import change_server_status

WAIT_TIME = 30 #seconds
MAX_NO_ATTEMPTS = 5
serverUUID = ""
isVerbose = False
ENDPOINT = "SERVER ENDPOINT"

#Login UUID/username/password
customerUUID=""
username=""
password=""

#Method used to authenticate a user with platform and create a token
def getToken(endpoint, username, cust_uuid, password):
    tokenURL = "%srest/user/current/authentication" % endpoint
    apiUserName = username + "/" + cust_uuid
    tokenPayload = {'automaticallyRenew': 'True'}
    tokenRequest = requests.get(tokenURL, params=tokenPayload,
                                auth=(apiUserName, password))

    retry = True
    count = 1

    #Try the request multiple times if failure occurs
    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):

        #Get response from reserver
        tokenRequest = requests.get(tokenURL, params=tokenPayload,
                                    auth=(apiUserName, password))
        #If the token is returned correctly, return it
        if tokenRequest.ok:
            token = tokenRequest.content
            tokenObj = json.loads(token)
            return tokenObj['publicToken']

        #If the server is busy, increment the count and try the request again
        if (tokenRequest.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            #If the server can not be reached, raise an exception
            raise Exception("Failed contacting %s with %s (%s)" % (
                tokenURL, tokenRequest.reason, tokenRequest.status_code))

    #If max amount of attempts have been reached, raise an exception
    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        raise Exception("HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server")

#Method used to create a new server instance on the platform
def rest_create_server(auth_parms, server_name, server_po_uuid, image_uuid, cluster_uuid, vdc_uuid, cpu_count,
                       ram_amount, nics, boot_disk_po_uuid, context_script):
    createURL = auth_parms['endpoint'] + "rest/user/current/resources/server"

    #Get image size
    img_ret = list_image(auth_parms, image_uuid)
    size = img_ret['size']

    #Set up parameters as required
    server_json = {
        "resourceName": server_name,
        "productOfferUUID": server_po_uuid,
        "imageUUID": image_uuid,
        "clusterUUID": cluster_uuid,
        "vdcUUID": vdc_uuid,
        "nics" : nics,
        "cpu": cpu_count,
        "ram": ram_amount,
        "disks": [{"iso": False,
                   # "resourceName": "the disk"
                   "resourceType": "DISK",
                   "resourceUUID": boot_disk_po_uuid,
                   "size": size,
                   "vdcUUID": vdc_uuid,
                   # "productOfferUUID": disk_po_uuid
                   }],
        "resourceType": "SERVER",
        "resourceMetadata": {"publicMetadata": context_script},
        # "serverCapabilities": ["CLONE", "CHILDREN_PERSIST_ON_DELETE", "CHILDREN_PERSIST_ON_REVERT"],
    }

    payload = server_json

    print(payload)
    payload_as_string = json.JSONEncoder().encode(payload)
    # Need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    #Submit server create request
    result = rest_submit_postrequest(createURL, payload_as_string, headers, auth_parms)
    return result


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

    #Check if image can be accessed properly
    result_set = rest_list_resource(auth_params, "image", sf)

    if result_set['totalCount'] == 0:
        raise RuntimeError("Image " + uuid + " not found or you do not have permissions to use it")

    print("==== Image Result ====")
    print result_set
    print("=========");
    # return just the first element (there was only one, right ?), otheriwse we end up doing e.g. img_ret['list'][0]['vdcUUID']
    # all over the place
    return result_set['list'][0]

#Method used to submit a REST POST request
def rest_submit_postrequest(theURL, payload, headers, auth_parms):
    retry = True
    count = 1

    #Attempt the request multiple times if failure occurs
    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):
        res = requests.post(theURL, payload, auth=(auth_parms['token'], ''), headers=headers)
        print("==============================================================")
        print "Request submitted, response URL and contents:"
        print(res.url)
        print res.content

        #jsonDump = json.dumps(res.content)
        jsonContent = json.loads(res.content)

        #Take the newly created serverUUID which is used later to create the server
        global serverUUID
        serverUUID = jsonContent["itemUUID"]

        print("HTTP response code: ", res.status_code)

        # Status 202 (Accepted) is good
        if ((res.status_code == 202) or (res.status_code == 200)):
            response = json.loads(res.content)
            retry = False
            return response

        #If server is busy, attempt the request again
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

    #If max amount of requests has been reached, print an error message
    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        print "HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server"
        # print(response['message'] + " (error code: " + response['errorCode'] + ")")

    return ""

#Use a REST request to list resources
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

    #If the request failed, retry the request a specified number of times
    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):

        if payload != None:
            res = requests.get(theURL, data=payload_as_string, auth=(auth_parms['token'], ''), headers=headers)
        else:
            res = requests.get(theURL, auth=(auth_parms['token'], ''), headers=headers)

        #Output the result from the request
        print("==============================================================")
        print(res.url)
        print("res=" + str(res))
        print res.content

        # Status 202 (Accepted) is good
        if (res.status_code == 200):
            response = json.loads(res.content)
            retry = False
            return response

        #If the server is busy, retry the request
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

    #Max number of requests has been reached
    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        raise RuntimeError("HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server")

    return ""


#Method used to create the server and deploy it to the platform
def create_server():

    hostname = ""

    #Get token to authenticate the user
    token = getToken(hostname, username,
                     customerUUID, password)

    auth = dict(endpoint=hostname, token=token)

    #Parameters that are to be sent to the platform. (Add/remove as required for target platform)
    auth_parms = auth
    server_name = ""
    server_productoffer_uuid = ""
    image_uuid = ""
    cluster_uuid = ""
    vdc_uuid = ""
    cpu_count = 1
    ram_amount = 512
    boot_disk_po_uuid = ""
    context_script = ""
    networkUUID = ""
    networkType = ""
    resourceName = ""
    resourceType = ""

    #NIC is a virtual resource that stands for Network Interface Card
    nic = {
       "clusterUUID": cluster_uuid,
       "networkUUID": networkUUID,
       "networkType": networkType,
       "resourceName": resourceName,
       "resourceType": resourceType,
       "vdcUUID": vdc_uuid,
    }

    nics = [
        nic
    ]

    #Call the create server method.  Modify parameters as required for the target platform
    rest_create_server(auth_parms, server_name, server_productoffer_uuid,
                       image_uuid, cluster_uuid,
                       vdc_uuid, cpu_count,
                       ram_amount, nics, boot_disk_po_uuid, context_script)

#Helper method used to change the state of a server into running mode
def start_server(auth_parms, server_uuid):
    """Function to start server, uuid in server_data"""
    server_state = get_server_state(auth_parms, server_uuid)
    if server_state == 'STOPPED':
        rc = change_server_status(auth_parms=auth_parms, server_uuid=server_uuid, state='RUNNING')
        if (rc != 0):
            raise Exception("Failed to put server " + server_uuid + " in to running state")

#The main method used to launch a server instance
def StartVM(customerUUID, customerUsername, customerPassword, serverUUID):
    #Authenticate the api connection
    auth_client = api_session(customerUsername, customerUUID, customerPassword)
    #Get the current server state
    server_state = get_server_state(auth_client, serverUUID)
    if (server_state == 'RUNNING'):
        print "Server is already running"
        return
    if (server_state == 'STOPPED' or server_state == 'STOPPING'):
        start_server(auth_client, serverUUID)
        print "Server is now RUNNING "
    else:
        print "Server could not be started because it is - %s " % server_state

#Method used to get api session
def api_session(customerUsername, customerUUID, customerPassword):
    """Function to set up api session, import credentials etc."""
    token = getToken(ENDPOINT, customerUsername, customerUUID, customerPassword)
    auth_client = dict(endpoint=ENDPOINT, token=token)
    return auth_client

create_server()
time.sleep(20)

StartVM(customerUUID,username,password,serverUUID)