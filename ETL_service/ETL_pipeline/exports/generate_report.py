"""
generate_rapport_pdf.py
Génère un rapport PDF structuré pour les pipelines ETL NUMERYX.
Appelé par la task Airflow rapport_pdf_task ou manuellement.
"""

import io
import json
from datetime import date, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Palette NUMERYX ──────────────────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#0f2044")
BLUE_MID    = colors.HexColor("#1a3a6b")
BLUE_LIGHT  = colors.HexColor("#2563eb")
BLUE_PALE   = colors.HexColor("#eff6ff")
GREEN       = colors.HexColor("#16a34a")
GREEN_PALE  = colors.HexColor("#f0fdf4")
RED         = colors.HexColor("#dc2626")
RED_PALE    = colors.HexColor("#fef2f2")
AMBER       = colors.HexColor("#d97706")
AMBER_PALE  = colors.HexColor("#fffbeb")
GRAY_LIGHT  = colors.HexColor("#f8fafc")
GRAY_MID    = colors.HexColor("#e2e8f0")
GRAY_TEXT   = colors.HexColor("#64748b")
WHITE       = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


# ── Styles ────────────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    s = {}

    s["title"] = ParagraphStyle(
        "title", fontSize=22, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=TA_LEFT, leading=28,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle", fontSize=10, textColor=colors.HexColor("#93c5fd"),
        fontName="Helvetica", alignment=TA_LEFT, leading=14,
    )
    s["section"] = ParagraphStyle(
        "section", fontSize=12, textColor=BLUE_DARK,
        fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
        borderPad=4,
    )
    s["body"] = ParagraphStyle(
        "body", fontSize=9, textColor=BLUE_DARK,
        fontName="Helvetica", leading=13,
    )
    s["small"] = ParagraphStyle(
        "small", fontSize=8, textColor=GRAY_TEXT,
        fontName="Helvetica", leading=11,
    )
    s["kpi_val"] = ParagraphStyle(
        "kpi_val", fontSize=20, textColor=BLUE_LIGHT,
        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=24,
    )
    s["kpi_lbl"] = ParagraphStyle(
        "kpi_lbl", fontSize=8, textColor=GRAY_TEXT,
        fontName="Helvetica", alignment=TA_CENTER, leading=10,
    )
    s["alert_title"] = ParagraphStyle(
        "alert_title", fontSize=9, textColor=RED,
        fontName="Helvetica-Bold", leading=12,
    )
    s["tag_ok"] = ParagraphStyle(
        "tag_ok", fontSize=8, textColor=GREEN,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
    )
    s["tag_err"] = ParagraphStyle(
        "tag_err", fontSize=8, textColor=RED,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
    )
    s["tag_warn"] = ParagraphStyle(
        "tag_warn", fontSize=8, textColor=AMBER,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
    )
    s["footer"] = ParagraphStyle(
        "footer", fontSize=7, textColor=GRAY_TEXT,
        fontName="Helvetica", alignment=TA_CENTER,
    )
    return s


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_sec(sec) -> str:
    if not sec:
        return "—"
    sec = float(sec)
    m, s = int(sec // 60), int(sec % 60)
    return f"{m}m {s}s" if m else f"{s}s"


def _fmt_num(n) -> str:
    if n is None:
        return "—"
    return f"{int(n):,}".replace(",", " ")


def _pct_bar_cell(pct: float, color=BLUE_LIGHT) -> Table:
    """Mini barre de progression dans une cellule de tableau."""
    pct = min(max(float(pct or 0), 0), 100)
    bar_w = 60 * mm
    filled = bar_w * pct / 100
    data = [[""]]
    t = Table(data, colWidths=[bar_w], rowHeights=[5])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_MID),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    return t


def _section_header(title: str, emoji: str, styles: dict):
    """Ligne titre de section avec barre colorée."""
    return [
        Spacer(1, 6 * mm),
        Table(
            [[Paragraph(f"{emoji}  {title}", styles["section"])]],
            colWidths=[PAGE_W - 2 * MARGIN],
            style=TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), BLUE_PALE),
                ("LEFTPADDING",  (0, 0), (-1, -1), 8),
                ("TOPPADDING",   (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
                ("LINEBELOW",    (0, 0), (-1, -1), 2, BLUE_LIGHT),
                ("ROUNDEDCORNERS", [4]),
            ]),
        ),
        Spacer(1, 3 * mm),
    ]


def _table_style_base():
    return TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 8),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("GRID",         (0, 0), (-1, -1), 0.3, GRAY_MID),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
    ])


# ── Page de couverture ────────────────────────────────────────────────────────

def _cover_page(story, report_date: str, styles: dict):
    # Bandeau bleu foncé
    header_data = [[
        Paragraph("NUMERYX", styles["title"]),
        Paragraph(f"Rapport ETL Journalier\n{report_date}", styles["subtitle"]),
    ]]
    header = Table(
        header_data,
        colWidths=[PAGE_W - 2 * MARGIN],
        rowHeights=[55 * mm],
        style=TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), BLUE_DARK),
            ("LEFTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",   (0, 0), (-1, -1), 18),
            ("SPAN",         (0, 0), (-1, -1)),
        ]),
    )
    story.append(header)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "Ce rapport présente une synthèse complète des pipelines ETL "
        "<b>BOAMP</b> et <b>DataGouv/SIRENE</b> : fiabilité des runs, "
        "volumes de données traitées, performance des tasks, qualité "
        "des données insérées et alertes détectées.",
        styles["body"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY_MID))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f"Généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')} · "
        "Projet PFE — École Polytechnique de Sousse",
        styles["small"],
    ))


# ── Section 1 : KPIs globaux ──────────────────────────────────────────────────

def _section_kpis(story, data: dict, styles: dict):
    story += _section_header("Vue d'ensemble", "📊", styles)

    runs       = data.get("runs", [])
    alertes    = data.get("alertes", {})
    volume     = data.get("volume", [])

    total_runs    = sum(r.get("total_runs",   0) for r in runs)
    success_runs  = sum(r.get("success_runs", 0) for r in runs)
    failed_runs   = sum(r.get("failed_runs",  0) for r in runs)
    success_rate  = round(success_runs / total_runs * 100) if total_runs else 0
    total_scraped = sum(v.get("total_raw", 0)          for v in volume)
    total_clean   = sum(v.get("total_clean_loaded", 0) for v in volume)
    nb_alertes    = (
        len(alertes.get("failed_tasks",  [])) +
        len(alertes.get("slow_tasks",    [])) +
        len(alertes.get("volume_alerts", []))
    )

    kpis = [
        (_fmt_num(total_runs),   "Runs exécutés"),
        (f"{success_rate}%",     "Taux de succès"),
        (_fmt_num(total_scraped),"Lignes scrappées"),
        (_fmt_num(total_clean),  "Lignes insérées"),
        (str(nb_alertes),        "Alertes"),
    ]

    cells = []
    for val, lbl in kpis:
        color = RED if (lbl == "Alertes" and nb_alertes > 0) else (
            GREEN if lbl == "Taux de succès" and success_rate >= 80 else BLUE_LIGHT
        )
        style = ParagraphStyle("kv", fontSize=18, textColor=color,
                               fontName="Helvetica-Bold", alignment=TA_CENTER)
        cells.append([
            Paragraph(val, style),
            Paragraph(lbl, styles["kpi_lbl"]),
        ])

    kpi_table = Table(
        [cells[i] for i in range(len(cells))],
        colWidths=[(PAGE_W - 2 * MARGIN)] * 1,
    )

    # Afficher en ligne
    row_data  = [[Paragraph(v, ParagraphStyle("kv2", fontSize=16, textColor=BLUE_LIGHT,
                  fontName="Helvetica-Bold", alignment=TA_CENTER)) for v, _ in kpis]]
    row_label = [[Paragraph(l, styles["kpi_lbl"]) for _, l in kpis]]
    col_w = (PAGE_W - 2 * MARGIN) / len(kpis)

    kpi_t = Table(
        row_data + row_label,
        colWidths=[col_w] * len(kpis),
        rowHeights=[20 * mm, 8 * mm],
        style=TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), BLUE_PALE),
            ("BOX",          (0, 0), (-1, -1), 0.5, GRAY_MID),
            ("LINEAFTER",    (0, 0), (-2, -1), 0.5, GRAY_MID),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]),
    )
    story.append(kpi_t)


# ── Section 2 : Runs & Fiabilité ─────────────────────────────────────────────

def _section_runs(story, data: dict, styles: dict):
    story += _section_header("Runs & Fiabilité", "🔄", styles)

    runs = data.get("runs", [])
    if not runs:
        story.append(Paragraph("Aucun run enregistré pour ce jour.", styles["small"]))
        return

    headers = ["DAG", "Total runs", "Succès", "Échecs", "Retries", "Durée moy.", "Durée max"]
    rows = [headers]
    for r in runs:
        state_ok  = int(r.get("success_runs", 0))
        state_err = int(r.get("failed_runs",  0))
        rows.append([
            r.get("dag_id", "—").replace("sync_", ""),
            str(int(r.get("total_runs", 0))),
            str(state_ok),
            str(state_err),
            str(int(r.get("total_retries", 0))),
            _fmt_sec(r.get("avg_duration_sec")),
            _fmt_sec(r.get("max_duration_sec")),
        ])

    col_w = (PAGE_W - 2 * MARGIN) / len(headers)
    t = Table(rows, colWidths=[col_w] * len(headers))
    ts = _table_style_base()

    # Colorier les cellules échec
    for i, row in enumerate(rows[1:], 1):
        if int(row[3]) > 0:
            ts.add("TEXTCOLOR", (3, i), (3, i), RED)
            ts.add("FONTNAME",  (3, i), (3, i), "Helvetica-Bold")
        if int(row[2]) > 0:
            ts.add("TEXTCOLOR", (2, i), (2, i), GREEN)

    t.setStyle(ts)
    story.append(t)


# ── Section 3 : Volume ────────────────────────────────────────────────────────

def _section_volume(story, data: dict, styles: dict):
    story += _section_header("Volume de Données", "🗄️", styles)

    volume = data.get("volume", [])
    if not volume:
        story.append(Paragraph("Aucune donnée de volume disponible.", styles["small"]))
        return

    headers = ["Run ID", "DAG", "Scrappé", "Raw chargé", "Clean inséré", "Rejeté", "Rétention raw", "Rétention clean"]
    rows = [headers]
    for v in volume:
        run_id_short = str(v.get("run_id", "—"))[-20:]
        rows.append([
            run_id_short,
            v.get("dag_id", "—").replace("sync_", ""),
            _fmt_num(v.get("total_raw")),
            _fmt_num(v.get("total_raw_loaded")),
            _fmt_num(v.get("total_clean_loaded")),
            _fmt_num(v.get("rejected")),
            f"{v.get('retention_raw_pct', 0)}%",
            f"{v.get('retention_clean_pct', 0)}%",
        ])

    col_widths = [35*mm, 22*mm, 20*mm, 22*mm, 24*mm, 18*mm, 24*mm, 24*mm]
    t = Table(rows, colWidths=col_widths)
    ts = _table_style_base()
    # Aligner les chiffres à droite
    for col in [2, 3, 4, 5]:
        ts.add("ALIGN", (col, 1), (col, -1), "RIGHT")
    t.setStyle(ts)
    story.append(t)

    # Comparaison semaine
    semaine = data.get("semaine", [])
    if semaine:
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("Comparaison semaine courante vs précédente", styles["section"]))
        headers2 = ["DAG", "Scrappé (S)", "Scrappé (S-1)", "Clean (S)", "Clean (S-1)", "Δ%"]
        rows2 = [headers2]
        for s in semaine:
            delta = s.get("delta_pct", 0)
            delta_str = f"+{delta}%" if delta >= 0 else f"{delta}%"
            rows2.append([
                s.get("dag_id", "—").replace("sync_", ""),
                _fmt_num(s.get("current_scraped")),
                _fmt_num(s.get("prev_scraped")),
                _fmt_num(s.get("current_clean")),
                _fmt_num(s.get("prev_clean")),
                delta_str,
            ])
        col_w2 = (PAGE_W - 2 * MARGIN) / len(headers2)
        t2 = Table(rows2, colWidths=[col_w2] * len(headers2))
        ts2 = _table_style_base()
        for i, row in enumerate(rows2[1:], 1):
            delta_val = float(row[5].replace("%", "").replace("+", "") or 0)
            color = GREEN if delta_val >= 0 else RED
            ts2.add("TEXTCOLOR", (5, i), (5, i), color)
            ts2.add("FONTNAME",  (5, i), (5, i), "Helvetica-Bold")
        t2.setStyle(ts2)
        story.append(t2)


# ── Section 4 : Performance ───────────────────────────────────────────────────

def _section_performance(story, data: dict, styles: dict):
    story += _section_header("Performance des Tasks", "⚡", styles)

    perf = data.get("performance", [])
    if not perf:
        story.append(Paragraph("Aucune donnée de performance disponible.", styles["small"]))
        return

    headers = ["DAG", "Task", "Exéc.", "Dur. moy.", "Dur. max", "CPU moy.", "RAM moy. (MB)", "Succès", "Échecs"]
    rows = [headers]

    SEUILS = {
        "scrape_boamp": 300, "extract_boamp": 120, "enrich_boamp": 180,
        "load_raw_boamp": 120, "clean_boamp": 180, "load_clean_boamp": 120,
        "scrape_sirene": 300, "extract_datagouv": 120, "load_raw_datagouv": 120,
        "clean_datagouv": 180, "load_clean_sirene": 120, "rapport_final": 60,
    }

    slow_rows = set()
    for i, p in enumerate(perf):
        seuil    = SEUILS.get(p.get("task_id", ""), 300)
        dur_avg  = float(p.get("dur_avg") or 0)
        is_slow  = dur_avg > seuil
        if is_slow:
            slow_rows.add(i + 1)

        rows.append([
            p.get("dag_id",  "—").replace("sync_", ""),
            p.get("task_id", "—"),
            str(int(p.get("executions", 0))),
            _fmt_sec(p.get("dur_avg")),
            _fmt_sec(p.get("dur_max")),
            f"{p.get('cpu_avg', 0)}%",
            f"{p.get('ram_avg_mb', 0)} MB",
            str(int(p.get("success_count", 0))),
            str(int(p.get("failed_count",  0))),
        ])

    col_widths = [22*mm, 36*mm, 14*mm, 18*mm, 18*mm, 16*mm, 26*mm, 16*mm, 16*mm]
    t = Table(rows, colWidths=col_widths)
    ts = _table_style_base()
    for i in slow_rows:
        ts.add("BACKGROUND", (0, i), (-1, i), AMBER_PALE)
        ts.add("TEXTCOLOR",  (3, i), (3, i), AMBER)
        ts.add("FONTNAME",   (3, i), (3, i), "Helvetica-Bold")
    for i, row in enumerate(rows[1:], 1):
        if int(row[8]) > 0:
            ts.add("TEXTCOLOR", (8, i), (8, i), RED)
            ts.add("FONTNAME",  (8, i), (8, i), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)
    if slow_rows:
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(
            "⚠ Les lignes en orange indiquent des tasks dont la durée dépasse le seuil défini.",
            styles["small"],
        ))


# ── Section 5 : Qualité ───────────────────────────────────────────────────────

def _section_qualite(story, data: dict, styles: dict):
    story += _section_header("Qualité des Données", "✅", styles)

    qualite = data.get("qualite", {})
    completude = qualite.get("completude", [])
    champs_null = qualite.get("champs_null", {})

    if completude:
        headers = ["Run ID", "Total entreprises", "Complétude moy.", "Min", "Max", "Incomplets (<50%)"]
        rows = [headers]
        for c in completude:
            rows.append([
                str(c.get("dag_run_id", "—"))[-18:],
                _fmt_num(c.get("total")),
                f"{c.get('completude_moy', 0)}%",
                f"{c.get('completude_min', 0)}%",
                f"{c.get('completude_max', 0)}%",
                _fmt_num(c.get("incomplets")),
            ])
        col_w = (PAGE_W - 2 * MARGIN) / len(headers)
        t = Table(rows, colWidths=[col_w] * len(headers))
        ts = _table_style_base()
        for i, row in enumerate(rows[1:], 1):
            pct = float(str(row[2]).replace("%", "") or 0)
            color = GREEN if pct >= 70 else (AMBER if pct >= 50 else RED)
            ts.add("TEXTCOLOR", (2, i), (2, i), color)
            ts.add("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")
        t.setStyle(ts)
        story.append(t)

    if champs_null:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Taux de champs manquants (NULL) dans la table entreprise", styles["section"]))
        sorted_fields = sorted(champs_null.items(), key=lambda x: x[1], reverse=True)
        headers2 = ["Champ", "% NULL", "Statut"]
        rows2 = [headers2]
        for field, pct in sorted_fields:
            statut = "✓ OK" if pct < 10 else ("⚠ Attention" if pct < 30 else "✗ Critique")
            rows2.append([field, f"{pct}%", statut])
        col_widths2 = [50*mm, 30*mm, 30*mm]
        t2 = Table(rows2, colWidths=col_widths2)
        ts2 = _table_style_base()
        for i, row in enumerate(rows2[1:], 1):
            pct_val = float(str(row[1]).replace("%", "") or 0)
            color = GREEN if pct_val < 10 else (AMBER if pct_val < 30 else RED)
            ts2.add("TEXTCOLOR", (2, i), (2, i), color)
            ts2.add("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")
        t2.setStyle(ts2)
        story.append(t2)


# ── Section 6 : Alertes ───────────────────────────────────────────────────────

def _section_alertes(story, data: dict, styles: dict):
    story += _section_header("Alertes & Anomalies", "🚨", styles)

    alertes      = data.get("alertes", {})
    failed_tasks = alertes.get("failed_tasks",  [])
    slow_tasks   = alertes.get("slow_tasks",    [])
    vol_alerts   = alertes.get("volume_alerts", [])

    if not failed_tasks and not slow_tasks and not vol_alerts:
        ok_box = Table(
            [[Paragraph("✓  Aucune alerte détectée — Tous les pipelines sont nominaux.", styles["body"])]],
            colWidths=[PAGE_W - 2 * MARGIN],
            style=TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), GREEN_PALE),
                ("LEFTPADDING",  (0, 0), (-1, -1), 10),
                ("TOPPADDING",   (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
                ("LINELEFT",     (0, 0), (0, -1), 3, GREEN),
            ]),
        )
        story.append(ok_box)
        return

    # Tasks échouées
    if failed_tasks:
        story.append(Paragraph("Tasks échouées", styles["alert_title"]))
        story.append(Spacer(1, 2*mm))
        headers = ["DAG", "Task", "Run ID", "Tentatives", "Durée"]
        rows = [headers]
        for f in failed_tasks:
            rows.append([
                f.get("dag_id",  "—").replace("sync_", ""),
                f.get("task_id", "—"),
                str(f.get("run_id", "—"))[-20:],
                str(f.get("try_number", 1)),
                _fmt_sec(f.get("duration")),
            ])
        col_w = (PAGE_W - 2 * MARGIN) / len(headers)
        t = Table(rows, colWidths=[col_w] * len(headers))
        ts = _table_style_base()
        ts.add("BACKGROUND", (0, 1), (-1, -1), RED_PALE)
        t.setStyle(ts)
        story.append(t)
        story.append(Spacer(1, 3*mm))

    # Tasks lentes
    if slow_tasks:
        story.append(Paragraph("Tasks lentes (dépassement seuil)", styles["alert_title"]))
        story.append(Spacer(1, 2*mm))
        headers = ["DAG", "Task", "Durée", "Seuil", "Dépassement"]
        rows = [headers]
        for s in slow_tasks:
            dur    = float(s.get("duration_sec") or 0)
            seuil  = float(s.get("seuil") or 300)
            excess = round(((dur - seuil) / seuil) * 100, 1)
            rows.append([
                s.get("dag_id",  "—").replace("sync_", ""),
                s.get("task_id", "—"),
                _fmt_sec(dur),
                _fmt_sec(seuil),
                f"+{excess}%",
            ])
        col_w = (PAGE_W - 2 * MARGIN) / len(headers)
        t = Table(rows, colWidths=[col_w] * len(headers))
        ts = _table_style_base()
        ts.add("BACKGROUND", (0, 1), (-1, -1), AMBER_PALE)
        ts.add("TEXTCOLOR",  (4, 1), (4, -1), AMBER)
        ts.add("FONTNAME",   (4, 1), (4, -1), "Helvetica-Bold")
        t.setStyle(ts)
        story.append(t)
        story.append(Spacer(1, 3*mm))

    # Chutes de volume
    if vol_alerts:
        story.append(Paragraph("Chutes de volume détectées (> 50% vs J-1)", styles["alert_title"]))
        story.append(Spacer(1, 2*mm))
        headers = ["DAG", "Volume aujourd'hui", "Volume J-1", "Chute"]
        rows = [headers]
        for v in vol_alerts:
            rows.append([
                v.get("dag_id", "—").replace("sync_", ""),
                _fmt_num(v.get("today")),
                _fmt_num(v.get("yesterday")),
                f"-{v.get('drop_pct', 0)}%",
            ])
        col_w = (PAGE_W - 2 * MARGIN) / len(headers)
        t = Table(rows, colWidths=[col_w] * len(headers))
        ts = _table_style_base()
        ts.add("BACKGROUND", (0, 1), (-1, -1), RED_PALE)
        ts.add("TEXTCOLOR",  (3, 1), (3, -1), RED)
        ts.add("FONTNAME",   (3, 1), (3, -1), "Helvetica-Bold")
        t.setStyle(ts)
        story.append(t)


# ── Footer ────────────────────────────────────────────────────────────────────

def _on_page(canvas, doc, report_date: str, styles: dict):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(BLUE_DARK)
    canvas.rect(0, 0, w, 12 * mm, fill=True, stroke=False)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN, 4 * mm,
        f"NUMERYX · Rapport ETL · {report_date}")
    canvas.drawRightString(w - MARGIN, 4 * mm,
        f"Page {doc.page}")
    canvas.restoreState()


# ── Point d'entrée principal ──────────────────────────────────────────────────

def generate_pdf(report_data: dict, report_date: str | None = None) -> bytes:
    """
    Génère le PDF en mémoire et retourne les bytes.

    Args:
        report_data: dict retourné par GET /api/rapport/complet/{day}
        report_date: date au format YYYY-MM-DD (défaut: aujourd'hui)

    Returns:
        bytes du PDF généré
    """
    if not report_date:
        report_date = date.today().isoformat()

    styles  = _styles()
    buffer  = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=20 * mm,
        title=f"Rapport ETL NUMERYX — {report_date}",
        author="NUMERYX Pipeline",
    )

    story = []

    # 1. Couverture
    _cover_page(story, report_date, styles)
    story.append(PageBreak())

    # 2. KPIs
    _section_kpis(story, report_data, styles)

    # 3. Runs
    _section_runs(story, report_data, styles)

    # 4. Volume
    story.append(PageBreak())
    _section_volume(story, report_data, styles)

    # 5. Performance
    story.append(PageBreak())
    _section_performance(story, report_data, styles)

    # 6. Qualité
    _section_qualite(story, report_data, styles)

    # 7. Alertes
    story.append(PageBreak())
    _section_alertes(story, report_data, styles)

    # Build
    doc.build(
        story,
        onFirstPage=lambda c, d: _on_page(c, d, report_date, styles),
        onLaterPages=lambda c, d: _on_page(c, d, report_date, styles),
    )

    return buffer.getvalue()