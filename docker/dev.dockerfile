FROM learningequality/kolibribase

ENV KOLIBRI_RUN_MODE=devserver
ENV KOLIBRI_HTTP_PORT=8000
# yarn devserver port is hardcoded to 8000 so this var is only for info purposes

COPY docker/entrypoint.py /docker/entrypoint.py

COPY . /kolibri
# This copies current source code into container, note code inside the container
# will not change if you change your working dir!
# For this you'll have to add option --volume $$PDW:/kolibri when running container.

WORKDIR /kolibri

ENTRYPOINT ["python", "/docker/entrypoint.py"]

# Install kolibri from source
RUN cd /kolibri \
    && pip3 install -e .

# Regenerate kolibri/VERSION from the current commit (rather than leaving any
# stale, gitignored copy that came in via `COPY . /kolibri` above). Kolibri's
# own "did the package version change" check - which drives whether it
# auto-applies new migrations against a persisted KOLIBRI_HOME on startup -
# reads this file first and never falls back to git if it's already present,
# so a stale file here means new migrations silently never get applied.
RUN cd /kolibri \
    && rm -f kolibri/VERSION \
    && python3 -c "import kolibri; print(kolibri.__version__)" > kolibri/VERSION

CMD ["yarn", "run", "devserver"]
