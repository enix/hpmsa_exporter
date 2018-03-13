FROM ubuntu:artful
MAINTAINER Antoine Millet <antoine.millet@enix.fr>

RUN apt update && apt install -y python3-lxml python3-prometheus-client python3-requests
COPY msa-exporter.py /bin/msa-exporter
RUN chmod +x /bin/msa-exporter

EXPOSE 8000
CMD /bin/msa-exporter "$HOST" "$LOGIN" "$PASSWORD"
