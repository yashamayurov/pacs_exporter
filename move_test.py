from pydicom.dataset import Dataset

from pynetdicom import AE, evt, StoragePresentationContexts, debug_logger
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelMove
import json
debug_logger()

all_series = []

def handle_store(event):
    """Handle a C-STORE service request"""
    # Ignore the request and return Success
    series = {}

    ds = event.dataset
#    ds.save_as(ds.SOPInstanceUID, write_like_original=False)

    
    series['AccessionNumber']       = json.loads(ds[0x0008, 0x0050].to_json())['Value'][0]
    series['StudyID']               = json.loads(ds[0x0020, 0x0010].to_json())['Value'][0]
    series['InstanceNumber']        = json.loads(ds[0x0020, 0x0013].to_json())['Value'][0]
    series['OrganDose']             = json.loads(ds[0x0040, 0x0316].to_json())['Value'][0]
    series['EntranceDoseInmGy']     = json.loads(ds[0x0040, 0x8302].to_json())['Value'][0]    
#    print(series)
    all_series.append(series)
    return 0x0000

def GetSeriesList(accession_number):
    handlers = [(evt.EVT_C_STORE, handle_store)]

    # Initialise the Application Entity
    ae = AE()

    # Add a requested presentation context
    ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)

    # Add the Storage SCP's supported presentation contexts
    ae.supported_contexts = StoragePresentationContexts

    # Start our Storage SCP in non-blocking mode, listening on port 11120
    ae.ae_title = 'TEST'
    scp = ae.start_server(("0.0.0.0", 11122), block=False, evt_handlers=handlers)

    # Create out identifier (query) dataset
    ds = Dataset()
    ds.QueryRetrieveLevel = 'SERIES'
    # Unique key for PATIENT level
    ds.add_new((0x0008,0x0050),'SH',accession_number)

    assoc = ae.associate("10.100.10.10", 104, ae_title="ARCHIMED")

    if assoc.is_established:
        # Use the C-MOVE service to send the identifier
        responses = assoc.send_c_move(ds, 'TEST', PatientRootQueryRetrieveInformationModelMove)

        for (status, identifier) in responses:
            if status:
                print('C-MOVE query status: 0x{0:04x}'.format(status.Status))
            else:
                print('Connection timed out, was aborted or received invalid response')

        # Release the association
        assoc.release()
    else:
        print('Association rejected, aborted or never connected')
    
    # Stop our Storage SCP
    scp.shutdown()
    return all_series

s = GetSeriesList('1866.4')
print(s)