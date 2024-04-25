from pydicom.dataset import Dataset
from datetime import datetime
from pynetdicom import AE, VerificationPresentationContexts
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind
import yaml
import time
import argparse

from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server
import prometheus_client

from datetime import date, timedelta



############

    # str = 'ASADOVA^ETAR^NARCHAKYIZYI'
    
    # str = str.split(' ')[0]
    # print(str)
local_AET = 'PYNETDICOM'
StudyDate = datetime.now().date().strftime("%Y%m%d")
IP = '10.100.10.10'#'10.0.0.20'
port = 104
AET='ARCHIMED'#'51STORAGE'
ae = AE(local_AET)
ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

# Create our Identifier (query) dataset
ds = Dataset()
#ds.PatientName = '*'

# if StudyID == '0':
#     ds.PatientName = patientName
# else:
#     ds.add_new((0x0020,0x0010),'SH',StudyID)

#(0008, 0050) Accession Number                    SH: '12140.11'

ds.QueryRetrieveLevel = 'STUDY'#'STUDY'
#ds.StudyDate = '20240410'
ds.add_new((0x0008,0x0050),'SH','1866.4')
#ds.add_new((0x0008,0x0080),'LO',InstitutionName)
assoc = ae.associate(IP, port, ae_title=AET)
if assoc.is_established:
    # Send the C-FIND request
    responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
    print(ds.to_json())
    # study_list = list(responses)
    # assoc.release()
    # study_list.pop()
    # print(study_list)       
else:
    print('Association rejected, aborted or never connected')