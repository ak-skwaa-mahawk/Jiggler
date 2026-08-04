sqlite3 -header -column tordial_gs.db "
SELECT 
    id, 
    datetime('now') as 'Current_Clock',
    runtime_env as 'Runtime_Identity', 
    node_count as 'Scale', 
    stability_score as 'Stability', 
    holonomy_norm as 'Global_||Ω||', 
    commutator_1_5 as 'Edge_[1][5]',
    CASE 
        WHEN quarantine_rate > 0.0 OR rollback_flag = 1 THEN '🛑 VETOED / ROLLBACK'
        ELSE '✅ Nominal Stability'
    END as 'Immune_Status'
FROM runs 
ORDER BY id DESC 
LIMIT 6;
"
