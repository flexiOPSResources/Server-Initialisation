# Server-creation-start
Python script to programatically create and start a server using the Flexiant Cloud Orchestrator platform.

These files include methods which can be configured to interface directly with the FCO API/Platform.  Once the script is properly configured, it can be utilised to create and launch a new server instance.

At the top of the serverCreationInitialisation.py file three variables must be set to an appropriate value.  The parameters are:

customerUUID (the UUID of the customer which is to obtain the new server instance)
username (the username of the customer)
password (the customers password)

The method create_server() contains the parameters which must be set in order for the script to create a new server instance.

These variables are:

**servername** (the name which is to be assigned to the new server)

**server_productoffer_uuid** (the product offer UUID which is to be assigned to the new server)

**image_uuid** (the UUID of the image which is to be initialised on the server)

**cluster_uuid** (the UUID of the cluster in which the server will belong to)

**vdc_uuid** (the UUID of the VDC in which the new server will belong to)

**cpu_count** (the number of CPUs the new server will have)

**ram_amount** (the amount of RAM the new server will have)

**boot_disk_po_uuid** (the UUID of the product offer of the boot disk which is to be used for the new server)

**context_script** (a context script to be run on the new server upon creation (optional))

**networkUUID** (the UUID of the network in which the NIC is to belong to)

**networkType** (the type of the network which the NIC is to operate on (e.g. IP))

**resourceName** (the name of the NIC resource)

**resourceType** (the type of the NIC resource)


Once these parameters are correctly set, the script will create and start a new server on the FCO platform for a specified customer.

