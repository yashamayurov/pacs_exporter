FROM python:3.6.8
LABEL maintainer="yakov@mayurov.ru"
RUN python3 -m pip install pyyaml prometheus_client pydicom pynetdicom
COPY pacs_exporter.py /pacs_exporter.py
COPY config.yml /config/config.yml
CMD ["python3","/pacs_exporter.py","--config", "/config/config.yml"]