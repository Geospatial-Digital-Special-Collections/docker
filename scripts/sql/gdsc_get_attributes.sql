-- FUNCTION: public.gdsc_get_attributes(regclass, numeric, numeric, text, text[], text)

-- DROP FUNCTION public.gdsc_get_attributes(regclass, numeric, numeric, text, text[], text);

CREATE OR REPLACE FUNCTION public.gdsc_get_attributes(
  tablename regclass,
  lat numeric,
  lng numeric,
  identifier text,
  attrs text[],
  normal text DEFAULT ''::text)
    RETURNS json
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
attributes_result record;
i integer;
attrlist text := '';
divisor text := '';
attrtype text := '';
srs_result record;

BEGIN

-- get the local srs
EXECUTE 'SELECT Find_SRID(''public'',''' || tablename || ''', ''geom_local'') AS srs;' INTO srs_result;

-- set the normalization string if present
IF normal != '' THEN 
  divisor := '/' || normal; 
  attrtype := '::numeric';
END IF;

-- make a list of all the attributes
FOR i IN 1 .. array_upper(attrs, 1)
LOOP
  attrlist := attrlist || attrs[i] || divisor || attrtype || ' AS ' || attrs[i] || ', '; 
END LOOP;
attrlist := identifier || ', ' || TRIM( TRAILING ', ' FROM attrlist);

-- perform the query
EXECUTE '
  SELECT ' || attrlist || ' FROM ' || tablename || '
  WHERE ST_Within(
    ST_Transform(ST_GeomFromText(''POINT(' || lng || ' ' || lat || ')'',4326), ' || srs_result.srs || '),
    ' || tablename || '.geom_local
  );
' INTO attributes_result;

RETURN json_agg(attributes_result);

END;
$BODY$;

ALTER FUNCTION public.gdsc_get_attributes(regclass, numeric, numeric, text, text[], text)
    OWNER TO postgres;
