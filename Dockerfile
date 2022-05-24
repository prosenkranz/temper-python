FROM python:3

WORKDIR /temper-python

COPY temperusb /temper-python/temperusb

COPY setup.py MANIFEST.in README.md /temper-python/

RUN apt-get update \
	&& apt-get install -y libusd-dev \
	&& apt-get clean

RUN python setup.py install --force

COPY etc/99-tempsensor.rules /usr/lib/udev/rules.d/

CMD temper-poll --prometheus-exporter
