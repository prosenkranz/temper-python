FROM python:3

WORKDIR /temper-python

COPY temperusb setup.py /temper-python/

RUN python setup.py install --force

COPY etc/99-tempsensor.rules /usr/lib/udev/rules.d/

CMD temper-poll --prometheus-exporter
