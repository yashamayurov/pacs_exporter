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

class DicomCollector(object):
    config = object()
    studyDate = ''
    local_AET = ''
    def __init__(self, config):
        self.config = config    
        self.local_AET = config['local_AET'] 
        pass

    def collect(self):
        sender_pacs = self.config['pacs_servers']['sender_pacs']
        target_pacs = self.config['pacs_servers']['target_pacs']
        
        sender_status = self.Check_echo(AET=sender_pacs['AET'],IP=sender_pacs['IP'],port=sender_pacs['port'])
        target_status = self.Check_echo(AET=target_pacs['AET'],IP=target_pacs['IP'],port=target_pacs['port'])

        if (sender_status + target_status == 2):
            self.studyDate = datetime.now().date().strftime("%Y%m%d")
            study_list = self.GetStudyList(StudyDate=self.studyDate,AET=sender_pacs['AET'],IP=sender_pacs['IP'],port=sender_pacs['port'])
            print(self.studyDate)
            print(sender_pacs)
            print(target_pacs)
            count_error = 0
            for study in study_list:
                ds = Dataset
                ds = study[1]
                is_error = self.CheckErrorSend(StudyDate=self.studyDate,AET=target_pacs['AET'],IP=target_pacs['IP'],port=target_pacs['port'],StudyID=ds.StudyID,patientName=ds.PatientName)
                count_error += is_error
            
                if is_error != 0:
                    print(is_error)
                    print(ds.PatientName)
                    print(ds.StudyID)  
                    gauge_send_study_error = GaugeMetricFamily("stydy_send_error","Name patient and Study ID", labels=['name_patient','study_id'])
                    gauge_send_study_error.add_metric([str(ds.PatientName),str(ds.StudyID)],1)
                    yield gauge_send_study_error

            gauge = GaugeMetricFamily("count_not_sended_study", "Number of studies that are not on the target server")
            gauge.add_metric(['count_not_sended_study'], count_error)
            yield gauge

        for server in self.config['pacs_servers'].items():
            
            r = self.Check_echo(AET=server[1]['AET'],IP=server[1]['IP'],port=server[1]['port'])
            print(server[1]['AET'],server[1]['IP'],server[1]['port'])
            gauge_server_status = GaugeMetricFamily("pacs_server_up","Server status", labels=['IP','AET','port'])
            gauge_server_status.add_metric([server[1]['IP'], server[1]['AET'], str(server[1]['port'])],r)
            yield gauge_server_status


    def GetStudyList(self, StudyDate, AET, IP, port, InstitutionName='',patientName='*',StudyID=''):
        ae = AE(self.local_AET)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

        # Create our Identifier (query) dataset
        ds = Dataset()
        #ds.PatientName = '*'
        if StudyID == '0':
            ds.PatientName = patientName
        else:
            ds.add_new((0x0020,0x0010),'SH',StudyID)
        ds.QueryRetrieveLevel = 'STUDY'
        ds.StudyDate = StudyDate
        ds.add_new((0x0008,0x0080),'LO',InstitutionName)
        assoc = ae.associate(IP, port, ae_title=AET)
        if assoc.is_established:
            # Send the C-FIND request
            responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
            study_list = list(responses)
            assoc.release()
            study_list.pop()
            return study_list        
        else:
            print('Association rejected, aborted or never connected')

    def GetCountStudyByInstName(self, StudyDate, AET, IP, port, InstitutionName='',StudyID=None):
        study_list = self.GetStudyList(StudyDate, AET, IP, port, InstitutionName)
        count_study = len(study_list) - 1 
        return count_study
    
    def CheckErrorSend(self,StudyDate, AET, IP, port, InstitutionName='',patientName='*',StudyID=''):
        study_list = self.GetStudyList( StudyDate=StudyDate, AET=AET, IP=IP, port=port, patientName=patientName,StudyID=StudyID)
        r = len(study_list)==0
        return int(r)
    
    def Check_echo(self, AET, IP, port):
        ae = AE(self.local_AET)
        # Add a requested presentation context
        ae.requested_contexts = VerificationPresentationContexts

        # Associate with peer AE at IP 127.0.0.1 and port 11112
        assoc = ae.associate(IP, port=port,ae_title=AET)
        result = False
        if assoc.is_established:
            # Use the C-ECHO service to send the request
            # returns the response status a pydicom Dataset
            status = assoc.send_c_echo()
            result = bool(status)
            # Check the status of the verification request
            assoc.release()
        return int(result)


############
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yml')

    args = parser.parse_args()
    config_file_name = args.config
    
    with open(config_file_name) as fh:
        read_data = yaml.load(fh, Loader=yaml.FullLoader)

    sender_pacs = read_data['pacs_servers']['sender_pacs']
    target_pacs = read_data['pacs_servers']['target_pacs']
        
    listen_port = read_data['listen_port']

    start_http_server(listen_port)
    print(f'I listen port {listen_port}')
    
    REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
    REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
    REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
    
    REGISTRY.register(DicomCollector(read_data))
    while True: 
        # period between collection
        time.sleep(3)

