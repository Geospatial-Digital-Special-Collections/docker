-- FUNCTION: public.gdsc_create_foreign_view(character varying, character varying)

-- DROP FUNCTION public.gdsc_create_foreign_view(character varying, character varying);

CREATE OR REPLACE FUNCTION public.gdsc_create_foreign_view(
  pod character varying,
  tablename character varying,
  viewname character varying)
    RETURNS json
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE 
serverid character varying := REPLACE(pod,'-','_');

BEGIN

EXECUTE 'CREATE SERVER ' || serverid || ' FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host ''' || pod || ''', dbname ''gdsc'', port ''5432'');';
EXECUTE 'CREATE USER MAPPING FOR postgres SERVER ' || serverid || ' OPTIONS (user ''__USER__'', password ''__PASS__'');';
EXECUTE 'CREATE USER MAPPING FOR sde SERVER ' || serverid || ' OPTIONS (user ''__USER__'', password ''__PASS__'');';
EXECUTE 'IMPORT FOREIGN SCHEMA public LIMIT TO (' || tablename || ') FROM SERVER ' || serverid || ' INTO remote;';
EXECUTE 'CREATE VIEW public.' || viewname || ' AS SELECT t.* FROM remote.' || tablename || ' t;';
EXECUTE 'GRANT SELECT ON ' || viewname || ' TO web_anon;';

RETURN '{"created view": "' || viewname || '"}';

END;
$BODY$;

ALTER FUNCTION public.gdsc_create_foreign_view(character varying, character varying, character varying)
    OWNER TO __USER__;