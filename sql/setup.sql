-- Normalize state abbreviations to full names in the olist database.
-- Run after exporting cleaned CSVs via EDA.ipynb.

UPDATE customers
SET customer_state = CASE customer_state
    WHEN 'AC' THEN 'Acre'
    WHEN 'AL' THEN 'Alagoas'
    WHEN 'AM' THEN 'Amazonas'
    WHEN 'AP' THEN 'Amapá'
    WHEN 'BA' THEN 'Bahia'
    WHEN 'CE' THEN 'Ceará'
    WHEN 'DF' THEN 'Distrito Federal'
    WHEN 'ES' THEN 'Espírito Santo'
    WHEN 'GO' THEN 'Goiás'
    WHEN 'MA' THEN 'Maranhão'
    WHEN 'MG' THEN 'Minas Gerais'
    WHEN 'MS' THEN 'Mato Grosso do Sul'
    WHEN 'MT' THEN 'Mato Grosso'
    WHEN 'PA' THEN 'Pará'
    WHEN 'PB' THEN 'Paraíba'
    WHEN 'PE' THEN 'Pernambuco'
    WHEN 'PI' THEN 'Piauí'
    WHEN 'PR' THEN 'Paraná'
    WHEN 'RJ' THEN 'Rio de Janeiro'
    WHEN 'RN' THEN 'Rio Grande do Norte'
    WHEN 'RO' THEN 'Rondônia'
    WHEN 'RR' THEN 'Roraima'
    WHEN 'RS' THEN 'Rio Grande do Sul'
    WHEN 'SC' THEN 'Santa Catarina'
    WHEN 'SE' THEN 'Sergipe'
    WHEN 'SP' THEN 'São Paulo'
    WHEN 'TO' THEN 'Tocantins'
    ELSE customer_state
END
WHERE customer_state IS NOT NULL;

UPDATE geolocation
SET geolocation_state = CASE geolocation_state
    WHEN 'AC' THEN 'Acre'
    WHEN 'AL' THEN 'Alagoas'
    WHEN 'AM' THEN 'Amazonas'
    WHEN 'AP' THEN 'Amapá'
    WHEN 'BA' THEN 'Bahia'
    WHEN 'CE' THEN 'Ceará'
    WHEN 'DF' THEN 'Distrito Federal'
    WHEN 'ES' THEN 'Espírito Santo'
    WHEN 'GO' THEN 'Goiás'
    WHEN 'MA' THEN 'Maranhão'
    WHEN 'MG' THEN 'Minas Gerais'
    WHEN 'MS' THEN 'Mato Grosso do Sul'
    WHEN 'MT' THEN 'Mato Grosso'
    WHEN 'PA' THEN 'Pará'
    WHEN 'PB' THEN 'Paraíba'
    WHEN 'PE' THEN 'Pernambuco'
    WHEN 'PI' THEN 'Piauí'
    WHEN 'PR' THEN 'Paraná'
    WHEN 'RJ' THEN 'Rio de Janeiro'
    WHEN 'RN' THEN 'Rio Grande do Norte'
    WHEN 'RO' THEN 'Rondônia'
    WHEN 'RR' THEN 'Roraima'
    WHEN 'RS' THEN 'Rio Grande do Sul'
    WHEN 'SC' THEN 'Santa Catarina'
    WHEN 'SE' THEN 'Sergipe'
    WHEN 'SP' THEN 'São Paulo'
    WHEN 'TO' THEN 'Tocantins'
    ELSE geolocation_state
END
WHERE geolocation_state IS NOT NULL;
