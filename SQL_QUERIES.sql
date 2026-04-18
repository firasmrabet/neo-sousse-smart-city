-- ============================================================================
-- 1. MESURES D'UN CAPTEUR (par UUID)
-- ============================================================================
SELECT 
    sm.id,
    sm.sensorId,
    sm.timestamp,
    sm.value,
    sm.unit,
    s.type as sensorType,
    s.status
FROM SensorMeasures sm
JOIN Sensor s ON sm.sensorId = s.uuid
WHERE sm.sensorId = '376e6436-0d6a-4334-ba01-276867685e48'
ORDER BY sm.timestamp DESC
LIMIT 5;


-- ============================================================================
-- 2. INTERVENTIONS AVEC LEURS TECHNICIENS
-- ============================================================================
SELECT 
    i.id as interventionId,
    i.sensorId,
    i.dateTime,
    i.type as interventionType,
    i.durationMinutes,
    i.cost,
    i.impactCo2,
    GROUP_CONCAT(t.name SEPARATOR ', ') as techniciens,
    GROUP_CONCAT(it.role SEPARATOR ', ') as roles
FROM Intervention i
LEFT JOIN InterventionTechnician it ON i.id = it.interventionId
LEFT JOIN Technician t ON it.technicianId = t.id
GROUP BY i.id
ORDER BY i.dateTime DESC;


-- ============================================================================
-- 

3. TRAJETS D'UN VÉHICULE (par plaque)
-- ============================================================================
SELECT 
    t.id as trajetId,
    t.plate,
    t.startLocation,
    t.endLocation,
    t.startTime,
    t.endTime,
    TIMEDIFF(t.endTime, t.startTime) as duration,
    t.distance,
    t.co2Emitted,
    v.brand,
    v.model,
    v.energy
FROM Trajet t
JOIN Vehicle v ON t.plate = v.plate
WHERE t.plate = '123-TN'
ORDER BY t.startTime DESC;


-- ============================================================================
-- 4. STATISTIQUES GLOBALES (Totaux)
-- ============================================================================
SELECT 
    (SELECT COUNT(*) FROM Citizen) as totalCitoyens,
    (SELECT COUNT(*) FROM Sensor) as totalCapteurs,
    (SELECT COUNT(*) FROM Vehicle) as totalVehicules,
    (SELECT COUNT(*) FROM Intervention) as totalInterventions,
    (SELECT COUNT(*) FROM Trajet) as totalTrajets,
    (SELECT COUNT(*) FROM Technician) as totalTechniciens,
    (SELECT COUNT(*) FROM Owner) as totalProprietaires,
    (SELECT COALESCE(SUM(cost), 0) FROM Intervention) as coutTotalInterventions,
    (SELECT COALESCE(SUM(impactCo2), 0) FROM Intervention) as co2SauvegardeParInterventions,
    (SELECT COALESCE(SUM(co2Emitted), 0) FROM Trajet) as co2EmisParTrajets;


-- ============================================================================
-- 5. CITOYENS LES PLUS ENGAGÉS (score d'engagement)
-- ============================================================================
SELECT 
    c.id,
    c.name,
    c.email,
    c.phone,
    c.engagementScore,
    c.mobilityPrefs,
    COUNT(co.id) as nombreConsultations,
    c.createdAt
FROM Citizen c
LEFT JOIN Consultation co ON c.id = co.citizenId
GROUP BY c.id
ORDER BY c.engagementScore DESC
LIMIT 20;



SELECT 
    i.id,
    i.sensorId,
    i.dateTime,
    i.type,
    i.durationMinutes,
    i.cost,
    i.impactCo2,
    MONTH(i.dateTime) as mois,
    YEAR(i.dateTime) as annee
FROM Intervention i
WHERE i.type = 'Prédictive'
AND MONTH(i.dateTime) = MONTH(CURDATE())
AND YEAR(i.dateTime) = YEAR(CURDATE())
ORDER BY i.dateTime DESC;

-- Résumé des économies prédictives ce mois
SELECT 
    COUNT(*) as nbInterventionsPredictives,
    COALESCE(SUM(cost), 0) as coutTotal,
    COALESCE(SUM(impactCo2), 0) as co2EconomiseeKg,
    COALESCE(AVG(durationMinutes), 0) as dureemoyenne
FROM Intervention
WHERE type = 'Prédictive'
AND MONTH(dateTime) = MONTH(CURDATE())
AND YEAR(dateTime) = YEAR(CURDATE());



SELECT 
    c.id,
    c.name,
    c.engagementScore,
    COUNT(co.id) as nombreConsultations,
    GROUP_CONCAT(co.topic SEPARATOR ', ') as sujets,
    MAX(co.createdAt) as derniereConsultation
FROM Citizen c
LEFT JOIN Consultation co ON c.id = co.citizenId
GROUP BY c.id
ORDER BY c.name;



SELECT 
    s.status,
    COUNT(*) as nombre,
    GROUP_CONCAT(s.type SEPARATOR ', ') as types,
    GROUP_CONCAT(s.uuid SEPARATOR ', ') as uuids
FROM Sensor s
GROUP BY s.status
ORDER BY s.status;


SELECT 
    v.plate,
    v.brand,
    v.model,
    v.energy,
    COUNT(t.id) as nombreTrajets,
    COALESCE(SUM(t.distance), 0) as distanceTotale,
    COALESCE(SUM(t.co2Emitted), 0) as co2Total,
    COALESCE(AVG(t.distance), 0) as distanceMoyenne
FROM Vehicle v
LEFT JOIN Trajet t ON v.plate = t.plate
GROUP BY v.plate
ORDER BY v.brand, v.model;



SELECT 
    o.id,
    o.name,
    o.email,
    o.ownerType,
    COUNT(s.uuid) as nombreCapteurs,
    GROUP_CONCAT(s.type SEPARATOR ', ') as typesCapteurs,
    GROUP_CONCAT(s.status SEPARATOR ', ') as statusCapteurs
FROM Owner o
LEFT JOIN Sensor s ON o.id = s.ownerId
GROUP BY o.id
ORDER BY o.name;



SELECT 
    t.id,
    t.name,
    COUNT(it.interventionId) as nombreInterventions,
    GROUP_CONCAT(i.type SEPARATOR ', ') as typesInterventions,
    COALESCE(SUM(i.cost), 0) as coutTotal,
    COALESCE(SUM(i.impactCo2), 0) as co2Economise
FROM Technician t
LEFT JOIN InterventionTechnician it ON t.id = it.technicianId
LEFT JOIN Intervention i ON it.interventionId = i.id
GROUP BY t.id
ORDER BY nombreInterventions DESC;



SELECT 
    p.id as IDPA,
    p.citizenId as IDCI,
    p.consultationId as IDCO,
    c.name as nomCitoyen,
    co.topic as sujetConsultation,
    co.mode,
    p.date,
    p.heure
FROM Participation p
JOIN Citizen c ON p.citizenId = c.id
JOIN Consultation co ON p.consultationId = co.id
ORDER BY p.date DESC, p.heure DESC;



SELECT 
    p.id as IDPA,
    p.citizenId as IDCI_participation,
    co.citizenId as IDCI_consultation,
    CASE 
        WHEN p.citizenId = co.citizenId THEN 'OK ✓'
        ELSE 'ERREUR ✗'
    END as verification,
    c.name,
    co.topic
FROM Participation p
JOIN Consultation co ON p.consultationId = co.id
JOIN Citizen c ON p.citizenId = c.id
ORDER BY p.id;



SELECT 
    c.id,
    c.name,
    c.address,
    c.phone,
    c.email,
    c.engagementScore,
    c.mobilityPrefs,
    COUNT(DISTINCT co.id) as nbConsultations,
    COUNT(DISTINCT p.id) as nbParticipations,
    GROUP_CONCAT(DISTINCT co.topic SEPARATOR ' | ') as sujets,
    GROUP_CONCAT(DISTINCT co.mode SEPARATOR ' | ') as modes
FROM Citizen c
LEFT JOIN Consultation co ON c.id = co.citizenId
LEFT JOIN Participation p ON c.id = p.citizenId
GROUP BY c.id
ORDER BY c.engagementScore DESC;



SELECT 
    DATE_FORMAT(NOW(), '%Y-%m') as mois,
    (SELECT COUNT(*) FROM Intervention WHERE MONTH(dateTime) = MONTH(NOW()) AND YEAR(dateTime) = YEAR(NOW())) as interventionsMois,
    (SELECT COUNT(*) FROM Intervention WHERE type = 'Prédictive' AND MONTH(dateTime) = MONTH(NOW()) AND YEAR(dateTime) = YEAR(NOW())) as predictivesMois,
    (SELECT COALESCE(SUM(cost), 0) FROM Intervention WHERE MONTH(dateTime) = MONTH(NOW()) AND YEAR(dateTime) = YEAR(NOW())) as coutInterventionsMois,
    (SELECT COALESCE(SUM(impactCo2), 0) FROM Intervention WHERE MONTH(dateTime) = MONTH(NOW()) AND YEAR(dateTime) = YEAR(NOW())) as co2SauvegardeeMois,
    (SELECT COUNT(*) FROM Trajet WHERE MONTH(startTime) = MONTH(NOW()) AND YEAR(startTime) = YEAR(NOW())) as trajetsMois,
    (SELECT COALESCE(SUM(distance), 0) FROM Trajet WHERE MONTH(startTime) = MONTH(NOW()) AND YEAR(startTime) = YEAR(NOW())) as distanceMois,
    (SELECT COALESCE(SUM(co2Emitted), 0) FROM Trajet WHERE MONTH(startTime) = MONTH(NOW()) AND YEAR(startTime) = YEAR(NOW())) as co2EmisesMois;
