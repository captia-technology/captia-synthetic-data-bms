# Grafana 11.4 con plugin redis-datasource para CAPTIA-SYNTHETIC-DATA-BMS.
# El provisioning y dashboards se montan vía bind mounts en compose para
# permitir hot-reload durante desarrollo.
FROM grafana/grafana:11.4.0

USER root
RUN grafana-cli plugins install redis-datasource
USER grafana
