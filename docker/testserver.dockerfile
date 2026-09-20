FROM learningequality/kolibribase

ENV KOLIBRI_RUN_MODE=testserver
ENV KOLIBRI_HTTP_PORT=8080

# psql is needed inside the container to run kolibri_helper_scripts'
# SQL-based tools (channel_module, channel_subscriptions, set_coach_content)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY docker/entrypoint.py /docker/entrypoint.py

COPY . /kolibri

WORKDIR /kolibri

ENTRYPOINT ["python", "/docker/entrypoint.py"]

# Install kolibri from source, add the postgres driver, and do a real
# production frontend build (unlike dev.dockerfile, this image does not
# run the webpack dev server at runtime - it serves pre-built static assets)
RUN cd /kolibri \
    && pip3 install -e . \
    && pip3 install -r requirements/postgres.txt \
    && yarn run build

CMD ["kolibri", "start", "--foreground"]
