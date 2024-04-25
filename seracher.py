from pydicom.dataset import Dataset

from pynetdicom import AE, evt, build_role, debug_logger
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelGet,
    CTImageStorage
)

debug_logger()

# Implement the handler for evt.EVT_C_STORE
def handle_store(event):
    """Handle a C-STORE request event."""
    ds = event.dataset
    ds.file_meta = event.file_meta

    # Save the dataset using the SOP Instance UID as the filename
    ds.save_as(ds.SOPInstanceUID, write_like_original=False)

    # Return a 'Success' status
    return 0x0000

handlers = [(evt.EVT_C_STORE, handle_store)]

# Initialise the Application Entity
ae = AE()

# Add the requested presentation contexts (QR SCU)
ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
# Add the requested presentation context (Storage SCP)
ae.add_requested_context(CTImageStorage)

# Create an SCP/SCU Role Selection Negotiation item for CT Image Storage
role = build_role(CTImageStorage, scp_role=True)

# Create our Identifier (query) dataset
# We need to supply a Unique Key Attribute for each level above the
#   Query/Retrieve level
ds = Dataset()
ds.QueryRetrieveLevel = 'IMAGE'
# Unique key for PATIENT level
ds.PatientID = '104136'
# Unique key for STUDY level
ds.StudyInstanceUID = '1.2.3'
# Unique key for SERIES level
ds.SeriesInstanceUID = '1.2.3.4'

# Associate with peer AE at IP 127.0.0.1 and port 11112
assoc = ae.associate("10.0.0.20", 11112,ae_title="51STORAGE")#, ext_neg=[role], evt_handlers=handlers)

if assoc.is_established:
    # Use the C-GET service to send the identifier
    responses = assoc.send_c_get(ds, PatientRootQueryRetrieveInformationModelGet)
    for (status, identifier) in responses:
        if status:
            print('C-GET query status: 0x{0:04x}'.format(status.Status))
        else:
            print('Connection timed out, was aborted or received invalid response')

    # Release the association
    assoc.release()
else:
    print('Association rejected, aborted or never connected')