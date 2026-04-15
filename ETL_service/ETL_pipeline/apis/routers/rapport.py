from fastapi import APIRouter
from sqlalchemy import text
from db.database import SessionLocal
from datetime import datetime, date, timedelta
import json
import io
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import text

from db.database import SessionLocal
from exports.generate_report import generate_pdf          # fichier précédent
router = APIRouter(prefix="/api/rapport", tags=["rapport"])

DAG_IDS = ["sync_boamp", "sync_datagouv"]


from decimal import Decimal

def _serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"{type(obj)} not serializable")


# ─────────────────────────────────────────────
#  HELPER — date cible
# ─────────────────────────────────────────────

def _target_date(day: str | None) -> date:
    if day:
        return date.fromisoformat(day)
    return date.today()


# ─────────────────────────────────────────────
#  1. RUNS & FIABILITÉ
# ─────────────────────────────────────────────

@router.get("/runs/{day}")
def get_runs_report(day: str | None = None):
    """
    Runs du jour par DAG :
    - nombre total, succès, échec
    - nombre de retries (try_number > 1)
    - run le plus long
    """
    target = _target_date(day)
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                dr.dag_id,
                COUNT(DISTINCT dr.run_id)                          AS total_runs,
                COUNT(DISTINCT dr.run_id) FILTER (
                    WHERE dr.state = 'success')                    AS success_runs,
                COUNT(DISTINCT dr.run_id) FILTER (
                    WHERE dr.state = 'failed')                     AS failed_runs,
                COUNT(ti.task_id) FILTER (
                    WHERE ti.try_number > 1)                       AS total_retries,
                MAX(EXTRACT(EPOCH FROM (dr.end_date - dr.start_date)))
                                                                   AS max_duration_sec,
                AVG(EXTRACT(EPOCH FROM (dr.end_date - dr.start_date)))
                                                                   AS avg_duration_sec
            FROM dag_run dr
            LEFT JOIN task_instance ti
                   ON ti.dag_id  = dr.dag_id
                  AND ti.run_id  = dr.run_id
            WHERE dr.dag_id = ANY(:dag_ids)
              AND dr.logical_date::date = :target
            GROUP BY dr.dag_id
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        return json.loads(json.dumps([dict(r) for r in rows], default=_serialize))
    finally:
        db.close()


@router.get("/runs/{day}/longest")
def get_longest_runs(day: str | None = None):
    """Top 5 runs les plus longs du jour."""
    target = _target_date(day)
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                dag_id,
                run_id,
                state,
                start_date,
                end_date,
                EXTRACT(EPOCH FROM (end_date - start_date)) AS duration_sec
            FROM dag_run
            WHERE dag_id = ANY(:dag_ids)
              AND logical_date::date = :target
              AND end_date IS NOT NULL
            ORDER BY duration_sec DESC
            LIMIT 5
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        return json.loads(json.dumps([dict(r) for r in rows], default=_serialize))
    finally:
        db.close()


@router.get("/retries/{day}")
def get_retries_detail(day: str | None = None):
    """Détail des tasks avec retry."""
    target = _target_date(day)
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                ti.dag_id,
                ti.task_id,
                ti.run_id,
                ti.try_number,
                ti.state,
                ti.start_date,
                ti.duration
            FROM task_instance ti
            WHERE ti.dag_id = ANY(:dag_ids)
              AND ti.start_date::date = :target
              AND ti.try_number > 1
            ORDER BY ti.try_number DESC
            LIMIT 20
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        return json.loads(json.dumps([dict(r) for r in rows], default=_serialize))
    finally:
        db.close()


# ─────────────────────────────────────────────
#  2. VOLUME DE DONNÉES
# ─────────────────────────────────────────────

@router.get("/volume/{day}")
def get_volume_report(day: str | None = None):
    """
    Volume par run et par phase via XCom :
    total_raw, total_raw_loaded, total_clean_loaded
    + lignes dans entreprise pour ce run
    """
    target = _target_date(day)
    db = SessionLocal()
    try:
        # XCom du jour
        xcoms = db.execute(text("""
            SELECT
                x.dag_id,
                x.run_id,
                x.task_id,
                x.key,
                x.value
            FROM xcom x
            JOIN dag_run dr
              ON dr.dag_id = x.dag_id
             AND dr.run_id = x.run_id
            WHERE x.dag_id = ANY(:dag_ids)
              AND dr.logical_date::date = :target
              AND x.key IN (
                  'total_raw', 'total_raw_loaded',
                  'total_clean_loaded', 'watermark_start'
              )
            ORDER BY x.dag_id, x.run_id, x.task_id
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        # Agréger par run
        runs = {}
        for x in xcoms:
            key = (x["dag_id"], x["run_id"])
            if key not in runs:
                runs[key] = {
                    "dag_id": x["dag_id"],
                    "run_id": x["run_id"],
                    "total_raw":          0,
                    "total_raw_loaded":   0,
                    "total_clean_loaded": 0,
                    "watermark":          None,
                }
            val = _parse_xcom(x["value"])
            if x["key"] == "total_raw":
                runs[key]["total_raw"] = max(runs[key]["total_raw"], int(val or 0))
            elif x["key"] == "total_raw_loaded":
                runs[key]["total_raw_loaded"] = max(runs[key]["total_raw_loaded"], int(val or 0))
            elif x["key"] == "total_clean_loaded":
                runs[key]["total_clean_loaded"] = max(runs[key]["total_clean_loaded"], int(val or 0))
            elif x["key"] == "watermark_start":
                runs[key]["watermark"] = str(val)

        # Calculer taux de rétention
        result = []
        for data in runs.values():
            raw_in   = data["total_raw"]
            raw_out  = data["total_raw_loaded"]
            clean    = data["total_clean_loaded"]
            rejected = raw_out - clean if raw_out >= clean else 0

            data["rejected"]          = rejected
            data["retention_raw_pct"] = round((raw_out / raw_in * 100), 1) if raw_in else 0
            data["retention_clean_pct"] = round((clean / raw_out * 100), 1) if raw_out else 0
            result.append(data)

        # Volume dans entreprise par dag_run_id
        ent = db.execute(text("""
            SELECT
                dag_run_id,
                COUNT(*) AS total_entreprises,
                ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy
            FROM entreprise
            WHERE date_scraping::date = :target
            GROUP BY dag_run_id
        """), {"target": target}).mappings().all()

        ent_map = {r["dag_run_id"]: dict(r) for r in ent}

        for data in result:
            ent_data = ent_map.get(data["run_id"], {})
            data["entreprises_total"]    = ent_data.get("total_entreprises", 0)
            data["completude_moy"]       = ent_data.get("completude_moy", 0)

        return result
    finally:
        db.close()


@router.get("/volume/semaine")
def get_weekly_volume():
    """Comparaison volume semaine courante vs semaine précédente."""
    db = SessionLocal()
    try:
        today      = date.today()
        week_start = today - timedelta(days=today.weekday())
        prev_start = week_start - timedelta(weeks=1)
        prev_end   = week_start - timedelta(days=1)

        def fetch_week(start, end):
            rows = db.execute(text("""
                SELECT
                    dr.dag_id,
                    SUM(CASE WHEN x.key = 'total_raw'
                        THEN CAST(x.value::text AS FLOAT) ELSE 0 END) AS total_scraped,
                    SUM(CASE WHEN x.key = 'total_clean_loaded'
                        THEN CAST(x.value::text AS FLOAT) ELSE 0 END) AS total_clean
                FROM xcom x
                JOIN dag_run dr ON dr.dag_id = x.dag_id AND dr.run_id = x.run_id
                WHERE dr.dag_id = ANY(:dag_ids)
                  AND dr.logical_date::date BETWEEN :start AND :end
                  AND x.key IN ('total_raw', 'total_clean_loaded')
                GROUP BY dr.dag_id
            """), {
                "dag_ids": DAG_IDS,
                "start":   start,
                "end":     end,
            }).mappings().all()
            return {r["dag_id"]: dict(r) for r in rows}

        current = fetch_week(week_start, today)
        previous = fetch_week(prev_start, prev_end)

        result = []
        for dag_id in DAG_IDS:
            curr = current.get(dag_id,  {"total_scraped": 0, "total_clean": 0})
            prev = previous.get(dag_id, {"total_scraped": 0, "total_clean": 0})

            scraped_delta = (
                round(((curr["total_scraped"] - prev["total_scraped"])
                       / prev["total_scraped"] * 100), 1)
                if prev["total_scraped"] else 0
            )

            result.append({
                "dag_id":          dag_id,
                "current_scraped": int(curr["total_scraped"] or 0),
                "current_clean":   int(curr["total_clean"]   or 0),
                "prev_scraped":    int(prev["total_scraped"] or 0),
                "prev_clean":      int(prev["total_clean"]   or 0),
                "delta_pct":       scraped_delta,
            })

        return result
    finally:
        db.close()


# ─────────────────────────────────────────────
#  3. PERFORMANCE — durée + ressources
# ─────────────────────────────────────────────

@router.get("/performance/{day}")
def get_performance_report(day: str | None = None):
    """
    Durée et ressources par task :
    - durée min/max/moyenne
    - CPU et RAM depuis XCom
    """
    target = _target_date(day)
    db = SessionLocal()
    try:
        # Durées par task
        tasks = db.execute(text("""
            SELECT
                ti.dag_id,
                ti.task_id,
                COUNT(*)                    AS executions,
                ROUND(MIN(ti.duration)::numeric, 2)  AS dur_min,
                ROUND(MAX(ti.duration)::numeric, 2)  AS dur_max,
                ROUND(AVG(ti.duration)::numeric, 2)  AS dur_avg,
                COUNT(*) FILTER (WHERE ti.state = 'success') AS success_count,
                COUNT(*) FILTER (WHERE ti.state = 'failed')  AS failed_count
            FROM task_instance ti
            WHERE ti.dag_id = ANY(:dag_ids)
              AND ti.start_date::date = :target
            GROUP BY ti.dag_id, ti.task_id
            ORDER BY ti.dag_id, dur_avg DESC
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        # Ressources XCom du jour
        resources = db.execute(text("""
            SELECT
                x.dag_id,
                x.task_id,
                x.key,
                AVG(CAST(x.value::text AS FLOAT)) AS avg_val,
                MAX(CAST(x.value::text AS FLOAT)) AS max_val
            FROM xcom x
            JOIN dag_run dr ON dr.dag_id = x.dag_id AND dr.run_id = x.run_id
            WHERE x.dag_id = ANY(:dag_ids)
              AND dr.logical_date::date = :target
              AND x.key IN ('cpu_used', 'ram_used_mb')
            GROUP BY x.dag_id, x.task_id, x.key
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        # Agréger les ressources par task
        res_map = {}
        for r in resources:
            k = (r["dag_id"], r["task_id"])
            if k not in res_map:
                res_map[k] = {}
            res_map[k][r["key"]] = {
                "avg": round(float(r["avg_val"] or 0), 1),
                "max": round(float(r["max_val"] or 0), 1),
            }

        result = []
        for t in tasks:
            k   = (t["dag_id"], t["task_id"])
            res = res_map.get(k, {})
            result.append({
                **dict(t),
                "cpu_avg":    res.get("cpu_used",    {}).get("avg", 0),
                "cpu_max":    res.get("cpu_used",    {}).get("max", 0),
                "ram_avg_mb": res.get("ram_used_mb", {}).get("avg", 0),
                "ram_max_mb": res.get("ram_used_mb", {}).get("max", 0),
            })

        return json.loads(json.dumps(result, default=_serialize))
    finally:
        db.close()


@router.get("/performance/tendance")
def get_duration_trend():
    """Tendance durée sur 7 jours — est-ce que ça ralentit ?"""
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                ti.dag_id,
                ti.task_id,
                DATE(ti.start_date)                  AS jour,
                ROUND(AVG(ti.duration)::numeric, 2)  AS dur_avg
            FROM task_instance ti
            WHERE ti.dag_id = ANY(:dag_ids)
              AND ti.start_date >= NOW() - INTERVAL '7 days'
              AND ti.state = 'success'
            GROUP BY ti.dag_id, ti.task_id, jour
            ORDER BY ti.dag_id, ti.task_id, jour
        """), {"dag_ids": DAG_IDS}).mappings().all()

        # Structurer par dag + task
        trend = {}
        for r in rows:
            k = f"{r['dag_id']}/{r['task_id']}"
            if k not in trend:
                trend[k] = {
                    "dag_id":  r["dag_id"],
                    "task_id": r["task_id"],
                    "points":  [],
                }
            trend[k]["points"].append({
                "date":    r["jour"].isoformat(),
                "dur_avg": float(r["dur_avg"] or 0),
            })

        return list(trend.values())
    finally:
        db.close()


# ─────────────────────────────────────────────
#  4. QUALITÉ DES DONNÉES
# ─────────────────────────────────────────────

@router.get("/qualite/{day}")
def get_quality_report(day: str | None = None):
    """
    Taux de complétude moyen, champs manquants, évolution.
    """
    target = _target_date(day)
    db = SessionLocal()
    try:
        # Complétude du jour par source
        completude = db.execute(text("""
            SELECT
                dag_run_id,
                DATE(date_scraping)                         AS jour,
                COUNT(*)                                    AS total,
                ROUND(AVG(taux_completude)::numeric, 2)     AS completude_moy,
                ROUND(MIN(taux_completude)::numeric, 2)     AS completude_min,
                ROUND(MAX(taux_completude)::numeric, 2)     AS completude_max,
                COUNT(*) FILTER (WHERE taux_completude < 50) AS incomplets
            FROM entreprise
            WHERE DATE(date_scraping) = :target
            GROUP BY dag_run_id, jour
        """), {"target": target}).mappings().all()

        # Champs les plus souvent NULL dans entreprise
        champs_null = db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE siren IS NULL)              AS null_siren,
                COUNT(*) FILTER (WHERE nom IS NULL)                AS null_nom,
                COUNT(*) FILTER (WHERE ville IS NULL)              AS null_ville,
                COUNT(*) FILTER (WHERE telephone IS NULL)          AS null_telephone,
                COUNT(*) FILTER (WHERE adresse_email IS NULL)      AS null_email,
                COUNT(*) FILTER (WHERE secteur_activite IS NULL)   AS null_secteur,
                COUNT(*) FILTER (WHERE ca IS NULL)                 AS null_ca,
                COUNT(*) FILTER (WHERE forme_juridique IS NULL)    AS null_forme,
                COUNT(*) FILTER (WHERE dirigeants IS NULL)         AS null_dirigeants,
                COUNT(*)                                           AS total
            FROM entreprise
            WHERE DATE(date_scraping) = :target
        """), {"target": target}).mappings().first()

        # Calculer les pourcentages de nullité
        fields_null = {}
        if champs_null and champs_null["total"]:
            total = champs_null["total"]
            for col in ["siren","nom","ville","telephone","email",
                        "secteur","ca","forme","dirigeants"]:
                val = champs_null[f"null_{col}"] or 0
                fields_null[col] = round((val / total) * 100, 1)

        # Évolution qualité 7 derniers jours
        evolution = db.execute(text("""
            SELECT
                DATE(date_scraping)                     AS jour,
                COUNT(*)                                AS total,
                ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy
            FROM entreprise
            WHERE date_scraping >= NOW() - INTERVAL '7 days'
            GROUP BY jour
            ORDER BY jour
        """)).mappings().all()

        return json.loads(json.dumps({
            "completude":  [dict(r) for r in completude],
            "champs_null": fields_null,
            "evolution":   [dict(r) for r in evolution],
        }, default=_serialize))
    finally:
        db.close()


# ─────────────────────────────────────────────
#  5. ALERTES & ANOMALIES
# ─────────────────────────────────────────────

@router.get("/alertes/{day}")
def get_alerts_report(day: str | None = None):
    """
    - Tasks échouées + message d'erreur
    - Tasks dont la durée dépasse un seuil
    - Chutes brutales de volume
    """
    target    = _target_date(day)
    yesterday = target - timedelta(days=1)
    db = SessionLocal()
    try:
        # Tasks échouées du jour
        failed = db.execute(text("""
            SELECT
                ti.dag_id,
                ti.task_id,
                ti.run_id,
                ti.start_date,
                ti.duration,
                ti.try_number
            FROM task_instance ti
            WHERE ti.dag_id = ANY(:dag_ids)
              AND ti.start_date::date = :target
              AND ti.state IN ('failed', 'upstream_failed')
            ORDER BY ti.start_date DESC
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        # Durées anormales — seuils par task (secondes)
        SEUILS = {
            "scrape_boamp":      300,   # 5 min
            "extract_boamp":     120,
            "enrich_boamp":      180,
            "load_raw_boamp":    120,
            "clean_boamp":       180,
            "load_clean_boamp":  120,
            "scrape_sirene":     300,
            "extract_datagouv":  120,
            "load_raw_datagouv": 120,
            "clean_datagouv":    180,
            "load_clean_sirene": 120,
            "rapport_final":     60,
        }

        slow_tasks = db.execute(text("""
            SELECT
                ti.dag_id,
                ti.task_id,
                ti.run_id,
                ROUND(ti.duration::numeric, 1) AS duration_sec,
                ti.start_date
            FROM task_instance ti
            WHERE ti.dag_id = ANY(:dag_ids)
              AND ti.start_date::date = :target
              AND ti.state = 'success'
              AND ti.duration IS NOT NULL
            ORDER BY ti.duration DESC
        """), {"dag_ids": DAG_IDS, "target": target}).mappings().all()

        slow = [
            {**dict(t), "seuil": SEUILS.get(t["task_id"], 300)}
            for t in slow_tasks
            if float(t["duration_sec"] or 0) > SEUILS.get(t["task_id"], 300)
        ]

        # Chutes de volume — comparer aujourd'hui vs hier via XCom
        def get_day_volume(d):
            rows = db.execute(text("""
                SELECT
                    x.dag_id,
                    SUM(CAST(x.value::text AS FLOAT)) AS total
                FROM xcom x
                JOIN dag_run dr ON dr.dag_id = x.dag_id AND dr.run_id = x.run_id
                WHERE x.dag_id = ANY(:dag_ids)
                  AND dr.logical_date::date = :target
                  AND x.key = 'total_raw'
                GROUP BY x.dag_id
            """), {"dag_ids": DAG_IDS, "target": d}).mappings().all()
            return {r["dag_id"]: int(r["total"] or 0) for r in rows}

        today_vol     = get_day_volume(target)
        yesterday_vol = get_day_volume(yesterday)

        volume_alerts = []
        for dag_id in DAG_IDS:
            t = today_vol.get(dag_id, 0)
            y = yesterday_vol.get(dag_id, 0)
            if y > 0 and t < y * 0.5:  # chute > 50%
                volume_alerts.append({
                    "dag_id":    dag_id,
                    "today":     t,
                    "yesterday": y,
                    "drop_pct":  round((1 - t / y) * 100, 1),
                })

        return json.loads(json.dumps({
            "failed_tasks":  [dict(r) for r in failed],
            "slow_tasks":    slow,
            "volume_alerts": volume_alerts,
        }, default=_serialize))
    finally:
        db.close()


# ─────────────────────────────────────────────
#  6. RAPPORT COMPLET (un seul appel)
# ─────────────────────────────────────────────

@router.get("/complet/{day}")
def get_full_report(day: str | None = None):
    """Toutes les sections en un seul appel."""
    target = day or date.today().isoformat()
    return {
        "date":        target,
        "runs":        get_runs_report(target),
        "volume":      get_volume_report(target),
        "performance": get_performance_report(target),
        "qualite":     get_quality_report(target),
        "alertes":     get_alerts_report(target),
        "semaine":     get_weekly_volume(),
    }


# ─────────────────────────────────────────────
#  HELPER XCom
# ─────────────────────────────────────────────

def _parse_xcom(raw):
    if raw is None:
        return 0
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, (bytes, memoryview)):
        raw = bytes(raw).decode('utf-8')
    if isinstance(raw, str):
        try:
            return float(json.loads(raw))
        except Exception:
            try:
                return float(raw)
            except Exception:
                return 0
    return 0

"""
rapport_pdf.py  — Router FastAPI
Génération, stockage et téléchargement des rapports PDF journaliers.

Routes :
  POST /api/rapport/pdf/generate/{day}   → génère + sauvegarde en DB
  GET  /api/rapport/pdf/download/{day}   → télécharge le PDF
  GET  /api/rapport/pdf/list             → liste tous les rapports
  GET  /api/rapport/pdf/latest           → dernier rapport disponible
"""

                # ton endpoint existant

router = APIRouter(prefix="/api/rapport/pdf", tags=["rapport-pdf"])


# ─────────────────────────────────────────────
#  HELPER serializer
# ─────────────────────────────────────────────

def _serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"{type(obj)} not serializable")


# ─────────────────────────────────────────────
#  CREATE TABLE (idempotent — appelle au démarrage)
# ─────────────────────────────────────────────

def ensure_reports_table():
    """Crée la table reports si elle n'existe pas."""
    db = SessionLocal()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS rapport_pdf (
                id           SERIAL PRIMARY KEY,
                report_date  DATE        NOT NULL UNIQUE,
                generated_at TIMESTAMP   NOT NULL DEFAULT NOW(),
                pdf_bytes    BYTEA       NOT NULL,
                file_size_kb INTEGER     GENERATED ALWAYS AS (
                                LENGTH(pdf_bytes) / 1024
                             ) STORED,
                nb_runs      INTEGER     DEFAULT 0,
                nb_alertes   INTEGER     DEFAULT 0,
                success_rate FLOAT       DEFAULT 0,
                summary_json JSONB       DEFAULT '{}'
            )
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reports_date
            ON reports (report_date DESC)
        """))
        db.commit()
    finally:
        db.close()


# ─────────────────────────────────────────────
#  ENDPOINT 1 — Générer + sauvegarder
# ─────────────────────────────────────────────

@router.post("/generate/{day}")
def generate_and_save_rapport(day: str | None = None):
    """
    Génère le rapport PDF du jour et le sauvegarde dans la table reports.
    Appelé automatiquement par Airflow à 23:55 via la task rapport_pdf_task.
    Peut aussi être appelé manuellement via l'UI.
    """
    report_date = day or date.today().isoformat()

    # 1. Récupérer toutes les données via l'endpoint complet existant
    try:
        report_data = get_full_report(report_date)
    except Exception as e:
        raise HTTPException(500, f"Erreur récupération données: {e}")

    # 2. Calculer les métriques résumées pour la table
    runs       = report_data.get("runs", [])
    alertes    = report_data.get("alertes", {})
    total_runs = sum(r.get("total_runs",   0) for r in runs)
    ok_runs    = sum(r.get("success_runs", 0) for r in runs)
    nb_alertes = (
        len(alertes.get("failed_tasks",  [])) +
        len(alertes.get("slow_tasks",    [])) +
        len(alertes.get("volume_alerts", []))
    )
    success_rate = round(ok_runs / total_runs * 100, 1) if total_runs else 0.0

    # 3. Générer le PDF
    try:
        pdf_bytes = generate_pdf(report_data, report_date)
    except Exception as e:
        raise HTTPException(500, f"Erreur génération PDF: {e}")

    # 4. Sauvegarder en base
    db = SessionLocal()
    try:
        summary = json.dumps({
            "total_runs":    total_runs,
            "success_rate":  success_rate,
            "nb_alertes":    nb_alertes,
            "volume":        [
                {
                    "dag_id":             v.get("dag_id"),
                    "total_raw":          v.get("total_raw", 0),
                    "total_clean_loaded": v.get("total_clean_loaded", 0),
                }
                for v in report_data.get("volume", [])
            ],
        }, default=_serialize)

        db.execute(text("""
            INSERT INTO rapport_pdf (
                report_date, generated_at, pdf_bytes,
                nb_runs, nb_alertes, success_rate, summary_json
            ) VALUES (
                :report_date, NOW(), :pdf_bytes,
                :nb_runs, :nb_alertes, :success_rate, :summary_json
            )
            ON CONFLICT (report_date) DO UPDATE SET
                generated_at = NOW(),
                pdf_bytes    = EXCLUDED.pdf_bytes,
                nb_runs      = EXCLUDED.nb_runs,
                nb_alertes   = EXCLUDED.nb_alertes,
                success_rate = EXCLUDED.success_rate,
                summary_json = EXCLUDED.summary_json
        """), {
            "report_date":  report_date,
            "pdf_bytes":    pdf_bytes,
            "nb_runs":      total_runs,
            "nb_alertes":   nb_alertes,
            "success_rate": success_rate,
            "summary_json": summary,
        })
        db.commit()

        return {
            "success":      True,
            "report_date":  report_date,
            "file_size_kb": round(len(pdf_bytes) / 1024, 1),
            "nb_runs":      total_runs,
            "nb_alertes":   nb_alertes,
            "success_rate": success_rate,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erreur sauvegarde: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────
#  ENDPOINT 2 — Télécharger un rapport
# ─────────────────────────────────────────────

@router.get("/download/{day}")
def download_rapport(day: str | None = None, inline: bool = False):
    """
    Télécharge le PDF du rapport pour la date donnée.
    Si non trouvé en base, le génère à la volée.
    """
    report_date = day or date.today().isoformat()

    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT pdf_bytes, generated_at
            FROM rapport_pdf
            WHERE report_date = :report_date
        """), {"report_date": report_date}).mappings().first()

        if row:
            pdf_bytes = bytes(row["pdf_bytes"])
        else:
            # Générer à la volée si pas encore en base
            try:
                result = generate_and_save_rapport(report_date)
            except Exception as e:
                raise HTTPException(404, f"Rapport non trouvé et génération impossible: {e}")

            row2 = db.execute(text("""
                SELECT pdf_bytes FROM rapport_pdf WHERE report_date = :d
            """), {"d": report_date}).mappings().first()

            if not row2:
                raise HTTPException(404, "Rapport introuvable")
            pdf_bytes = bytes(row2["pdf_bytes"])

        filename = f"rapport_etl_numeryx_{report_date}.pdf"
        disposition = "inline" if inline else "attachment"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'{disposition}; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    finally:
        db.close()


# ─────────────────────────────────────────────
#  ENDPOINT 3 — Liste des rapports disponibles
# ─────────────────────────────────────────────

@router.get("/list")
def list_rapports(limit: int = 30, start_date: str | None = None, end_date: str | None = None):
    """Retourne la liste des rapports générés (sans les PDF bytes)."""
    db = SessionLocal()
    try:
        query = """
            SELECT
                report_date,
                generated_at,
                file_size_kb,
                nb_runs,
                nb_alertes,
                success_rate,
                summary_json
            FROM rapport_pdf
            WHERE 1=1
        """
        params = {"limit": limit}
        
        if start_date:
            query += " AND report_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND report_date <= :end_date"
            params["end_date"] = end_date
            
        query += " ORDER BY report_date DESC LIMIT :limit"

        rows = db.execute(text(query), params).mappings().all()

        return json.loads(json.dumps(
            [dict(r) for r in rows],
            default=_serialize,
        ))
    finally:
        db.close()


# ─────────────────────────────────────────────
#  ENDPOINT 4 — Dernier rapport
# ─────────────────────────────────────────────

@router.get("/latest")
def get_latest_rapport():
    """Retourne les métadonnées du dernier rapport généré."""
    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT report_date, generated_at, file_size_kb,
                   nb_runs, nb_alertes, success_rate, summary_json
            FROM reports
            ORDER BY report_date DESC
            LIMIT 1
        """)).mappings().first()

        if not row:
            return {"available": False}

        return json.loads(json.dumps(
            {"available": True, **dict(row)},
            default=_serialize,
        ))
    finally:
        db.close()