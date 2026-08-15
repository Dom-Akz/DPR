-- Set thresholds for KRIs that don't have one
UPDATE dashboard_indicator 
SET risk_threshold = 50.00 
WHERE kind = 'KRI' 
AND risk_threshold IS NULL;

-- Add measurements to KRIs that don't have any
INSERT INTO dashboard_indicatormeasurement (indicator_id, value, calculated_at)
SELECT 
    i.id,
    (random() * 80 + 10)::numeric(10,2) as value,
    NOW() - (random() * 365 * interval '1 day') as calculated_at
FROM dashboard_indicator i
WHERE i.kind = 'KRI'
AND NOT EXISTS (
    SELECT 1 FROM dashboard_indicatormeasurement m 
    WHERE m.indicator_id = i.id
);

-- Check how many measurements were added
SELECT 
    i.id,
    i.name,
    COUNT(m.id) as measurement_count
FROM dashboard_indicator i
LEFT JOIN dashboard_indicatormeasurement m ON i.id = m.indicator_id
WHERE i.kind = 'KRI'
GROUP BY i.id, i.name
ORDER BY measurement_count DESC;

