-- Initialize Ukrainian FTS (Hunspell) on first DB creation.
CREATE TEXT SEARCH DICTIONARY IF NOT EXISTS ukrainian_hunspell (
    TEMPLATE = ispell,
    DictFile = uk_UA,
    AffFile = uk_UA
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'ukrainian') THEN
        CREATE TEXT SEARCH CONFIGURATION ukrainian (COPY = simple);
    END IF;
END
$$;

ALTER TEXT SEARCH CONFIGURATION ukrainian
    ALTER MAPPING FOR word, hword, hword_part, hword_numpart
    WITH ukrainian_hunspell;
