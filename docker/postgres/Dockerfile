FROM pgvector/pgvector:pg16

RUN apt-get update \
    && apt-get install -y --no-install-recommends hunspell-uk hunspell \
    && rm -rf /var/lib/apt/lists/*

# Make hunspell dictionaries available to PostgreSQL tsearch.
RUN mkdir -p /usr/share/postgresql/16/tsearch_data \
    && cp /usr/share/hunspell/uk_UA.aff /usr/share/postgresql/16/tsearch_data/uk_UA.aff \
    && cp /usr/share/hunspell/uk_UA.dic /usr/share/postgresql/16/tsearch_data/uk_UA.dic

COPY init/ /docker-entrypoint-initdb.d/
