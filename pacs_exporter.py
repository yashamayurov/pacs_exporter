from pydicom.dataset import Dataset
from datetime import datetime
from pynetdicom import AE
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind
import yaml
import time
import argparse

from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server

class DicomCollector(object):
    config = object()
    studyDate = ''
    def __init__(self, sdate, config):
        self.config = config
        self.studyDate = sdate
        pass
    
    def collect(self):
        sender_pacs = self.config['pacs_servers']['sender_pacs']
        target_pacs = self.config['pacs_servers']['target_pacs']
        study_list = self.GetStudyList(StudyDate=self.studyDate,AET=sender_pacs['AET'],IP=sender_pacs['IP'],port=sender_pacs['port'])
        print(self.studyDate)
        print(sender_pacs)
        print(target_pacs)
        count_error = 0
        for study in study_list:
            ds = Dataset
            ds = study[1]
    #mokb_study_list = GetStudyList('20221017','51STORAGE','10.0.0.20',11112,StudyID=ds.StudyID,patientName=ds.PatientName)
            is_error = self.CheckErrorSend(StudyDate=self.studyDate,AET=target_pacs['AET'],IP=target_pacs['IP'],port=target_pacs['port'],StudyID=ds.StudyID,patientName=ds.PatientName)
            count_error += is_error
        
            if is_error != 0:
                print(is_error)
                print(ds.PatientName)
                print(ds.StudyID)  
            

        gauge = GaugeMetricFamily("count_not_sended_study", "Number of studies that are not on the target server")
        gauge.add_metric(['count_not_sended_study'], count_error)
        yield gauge
        # count = CounterMetricFamily("random_number_2", "A random number 2.0", labels=['randomNum'])
        # global totalRandomNumber
        # totalRandomNumber += random.randint(1,30)
        # count.add_metric(['random_num'], totalRandomNumber)
        # yield count

    def GetStudyList(self, StudyDate, AET, IP, port, InstitutionName='',patientName='*',StudyID=''):
        ae = AE()
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
    
    study_date = datetime.now().date().strftime("%Y%m%d")
    listen_port = read_data['listen_port']


    start_http_server(listen_port)
    print(f'I listen port {listen_port}')
    REGISTRY.register(DicomCollector(study_date,read_data))
    while True: 
        # period between collection
        time.sleep(3)

#print(a['ip'])

#study_list = GetStudyList('20221018','ARCHIMED','10.100.10.10',104)

# study_list = GetStudyList(date,sender_pacs['AET'],sender_pacs['IP'],sender_pacs['port'])

# count_error = 0
# for study in study_list:
#     ds = Dataset
#     ds = study[1]
    
#     #mokb_study_list = GetStudyList('20221017','51STORAGE','10.0.0.20',11112,StudyID=ds.StudyID,patientName=ds.PatientName)
#     is_error = CheckErrorSend(date,target_pacs['AET'],target_pacs['IP'],target_pacs['port'],StudyID=ds.StudyID,patientName=ds.PatientName)
#     count_error += is_error
#     if is_error != 0:
#         print(is_error)
#         print(ds.PatientName)
#         print(ds.StudyID)

# print(count_error)