FROM ubuntu:20.04
MAINTAINER Antoine Millet <antoine.millet@enix.fr>

RUN apt update && apt install -y python3-lxml python3-prometheus-client python3-requests
COPY msa_exporter.py /bin/msa_exporter
RUN chmod +x /bin/msa_exporter

EXPOSE 8000
CMD /bin/msa_exporter "$HOST" "$LOGIN" "$PASSWORD"
