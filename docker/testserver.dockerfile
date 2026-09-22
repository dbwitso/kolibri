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

# Regenerate kolibri/VERSION from the current commit (rather than leaving any
# stale, gitignored copy that came in via `COPY . /kolibri` above). Kolibri's
# own "did the package version change" check - which drives whether it
# auto-applies new migrations against the persisted database on startup -
# reads this file first and never falls back to git if it's already present,
# so a stale file here means new migrations silently never get applied on a
# rebuild/redeploy.
RUN cd /kolibri \
    && rm -f kolibri/VERSION \
    && python3 -c "import kolibri; print(kolibri.__version__)" > kolibri/VERSION

CMD ["kolibri", "start", "--foreground"]
