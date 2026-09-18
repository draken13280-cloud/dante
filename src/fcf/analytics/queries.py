summary_sql = {
    "time_per_sku": """
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM finished_at - started_at)) AS p50_s,
       percentile_cont(0.9) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM finished_at - started_at)) AS p90_s
FROM jobs WHERE status = 'done' AND mode = :mode AND created_at > :since
""",
    "first_pass_rate": """
SELECT a.kind, a.channel,
       COUNT(*) FILTER (WHERE q.verdict = 'pass')::float / COUNT(*) AS first_pass_rate
FROM assets a
JOIN runs r ON r.id = a.run_id AND r.version = 1
JOIN LATERAL (SELECT verdict FROM qa_reports WHERE asset_id = a.id ORDER BY created_at LIMIT 1) q ON TRUE
WHERE a.created_at > :since GROUP BY 1, 2
""",
    "top_failing_rules": """
SELECT c->>'rule' AS rule, c->>'severity' AS severity, COUNT(*) AS failures
FROM qa_reports, LATERAL jsonb_array_elements(checks) c
WHERE (c->>'passed')::bool = false AND created_at > :since
GROUP BY 1, 2 ORDER BY failures DESC LIMIT 20
""",
    "cost_by_provider": """
SELECT payload->>'provider' AS provider, SUM((payload->>'cost_cents')::int) AS cents,
       COUNT(DISTINCT job_id) AS jobs
FROM events WHERE type = 'provider.call' AND ts > :since GROUP BY 1
""",
    "publish_by_platform": """
SELECT platform, status, COUNT(*) FROM publish_attempts WHERE created_at > :since GROUP BY 1, 2
""",
}
