FROM python:3.8.1-slim
COPY ./requirements.txt /usr/local/src/seckrit/requirements.txt
RUN pip3 install -r /usr/local/src/seckrit/requirements.txt
COPY ./src /usr/local/src/seckrit
ENTRYPOINT ["python3", "/usr/local/src/seckrit/seckrit.py"]