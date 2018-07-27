FROM python:3-alpine

WORKDIR /opt/logreposit/bmv-reader-service

ADD src/bmv_reader.py         /opt/logreposit/bmv-reader-service/bmv_reader.py
ADD src/bmv_reader_service.py /opt/logreposit/bmv-reader-service/bmv_reader_service.py
ADD src/bmv_reading.py        /opt/logreposit/bmv-reader-service/bmv_reading.py

RUN pip install requests pyserial

CMD [ "python", "-u", "./bmv_reader_service.py"  ]
