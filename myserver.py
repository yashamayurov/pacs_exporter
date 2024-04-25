from pynetdicom import AE, evt, AllStoragePresentationContexts, debug_logger
import json

debug_logger()

# Implement a handler for evt.EVT_C_STORE
def GetSeriesDate(ds):
    # data = {}
    # data["SOPInstanceUID"]      = ds.SOPInstanceUID
    
    # AccNumber = {}
    # AccNumber = ds[0x0008, 0x0050].to_json()
    j = json.loads(ds.to_json())
    return j
    # data["AccessionNumber"]     = j["Value"]
    # data["OrganDose"]           = ds[0x0040, 0x0316].to_json()
    # data["EntranceDoseinmGy"]   = ds[0x0040, 0x8302].to_json()
    # return data
  
def handle_store(event):
    """Handle a C-STORE request event."""
    # Decode the C-STORE request's *Data Set* parameter to a pydicom Dataset
    ds = event.dataset

    # Add the File Meta Information
    ds.file_meta = event.file_meta
    #print(ds)
    #myJson = ds[0x00080008].to_json();
    
    # print("$$$$$$$$$$$")
    # print(ds.SOPInstanceUID)
    # print(ds[0x0008, 0x0050].to_json())
    # print(ds[0x0040, 0x0316].to_json())
    # print(ds[0x0040, 0x8302].to_json())
    res = GetSeriesDate(ds)
    print(res)
    #print(ds)
    # Save the dataset using the SOP Instance UID as the filename
    #ds.save_as(ds.SOPInstanceUID, write_like_original=True)

    # Return a 'Success' status
    return 0x0000

handlers = [(evt.EVT_C_STORE, handle_store)]

# Initialise the Application Entity
ae = AE("TEST")

# Support presentation contexts for all storage SOP Classes
ae.supported_contexts = AllStoragePresentationContexts

# Start listening for incoming association requests
ae.start_server(("0.0.0.0", 11122), evt_handlers=handlers)