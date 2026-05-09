# Grafana 11.4 con plugin redis-datasource para CAPTIA-SYNTHETIC-DATA-BMS.
# El provisioning y dashboards se montan vía bind mounts en compose para
# permitir hot-reload durante desarrollo.
FROM grafana/grafana:13.0.1

USER root
RUN grafana-cli plugins install redis-datasource
USER grafana
