FROM python:latest
COPY /src /usr/local/src/seckrit
COPY /requirements.txt /usr/local/src/seckrit/requirements.txt
RUN pip3 install -r /usr/local/src/seckrit/requirements.txt
CMD python3 /usr/local/src/seckrit/seckrit.py /etc/seckrit/manifest.yml