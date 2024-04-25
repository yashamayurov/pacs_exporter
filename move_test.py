from pydicom.dataset import Dataset

from pynetdicom import AE, evt, StoragePresentationContexts, debug_logger
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelMove
import json
debug_logger()

class study_info(object):
    all_series = []
    config = {}
    
    def __init__(self,config) -> None:
        self.config = config
        pass

    def handle_store(self,event):
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
        self.all_series.append(series)
        return 0x0000

    def GetSeriesListByAccessionNumber(self, accession_number):
        handlers = [(evt.EVT_C_STORE, self.handle_store)]

        # Initialise the Application Entity
        ae = AE()

        # Add a requested presentation context
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)

        # Add the Storage SCP's supported presentation contexts
        ae.supported_contexts = StoragePresentationContexts

        # Start our Storage SCP in non-blocking mode, listening on port 11120
        #ae.ae_title = 'TEST'
        local_ae  = self.config["local_ae"]
        ae.ae_title = local_ae["ae"]
        scp = ae.start_server((local_ae["ip"], local_ae["port"]), block=False, evt_handlers=handlers)

        # Create out identifier (query) dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = 'SERIES'
        # Unique key for PATIENT level
        ds.add_new((0x0008,0x0050),'SH',accession_number)

        called_ae = self.config["called_ae"]
#        assoc = ae.associate("10.100.10.10", 104, ae_title="ARCHIMED")
        assoc = ae.associate(called_ae["ip"], called_ae["port"], ae_title=called_ae["ae"])
        
        if assoc.is_established:
            # Use the C-MOVE service to send the identifier
            responses = assoc.send_c_move(ds, local_ae["ae"], PatientRootQueryRetrieveInformationModelMove)
            
            for (status, identifier) in responses:
                print(identifier)
                print(status)
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
        return self.all_series



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
            print(identifier)
            print(status.Status)
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
config = {"local_ae":
            {"ip":"0.0.0.0",
             "port":11122,
             "ae":"TEST"},
          "called_ae":
            {"ip":"10.100.10.10",
             "port":104,
             "ae":"ARCHIMED"}
            }
#st_info = study_info(config=config)
#s = st_info.GetSeriesListByAccessionNumber('1866.4')
print(s)