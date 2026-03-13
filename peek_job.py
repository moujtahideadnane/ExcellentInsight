
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.config import get_settings
from app.models.job import AnalysisJob

async def peek_latest_job():
    # Load .env
    env_path = Path('.env')
    load_dotenv(dotenv_path=env_path)
    
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Get the latest job
        stmt = select(AnalysisJob).order_by(desc(AnalysisJob.created_at)).limit(1)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            print("No jobs found.")
            return

        print(f"--- Job ID: {job.id} ---")
        print(f"Status: {job.status}")
        print(f"File Name: {job.file_name}")
        print("-" * 20)

        # 1. Schema Result
        schema = job.schema_result or {}
        print("\n[Actual Database Schema]")
        for sheet in schema.get("sheets", []):
            columns = [c["name"] for c in sheet.get("columns", [])]
            print(f"Sheet '{sheet['name']}':")
            print(f"  Columns: {columns}")
        
        # 2. LLM Result
        llm_res = job.llm_result or {}
        print("\n[LLM Enrichment Result]")
        print(f"Domain: {llm_res.get('domain')}")
        print(f"Summary: {llm_res.get('summary')}")
        
        print("\nKPIs Suggestions:")
        for kpi in llm_res.get("kpis", []):
            print(f"  - {kpi.get('label')}: formula='{kpi.get('formula')}', sheet='{kpi.get('sheet')}'")
        
        # Chart Suggestions:
        for chart in llm_res.get("charts", []):
            print(f"  - {chart.get('title')}: x='{chart.get('x_axis')}', y='{chart.get('y_axis')}', sheet='{chart.get('sheet')}'")

        # 3. Dashboard Config
        dbg_config = job.dashboard_config or {}
        print("\n[Dashboard Config]")
        print(f"KPI Count: {len(dbg_config.get('kpis', []))}")
        print(f"Chart Count: {len(dbg_config.get('charts', []))}")
        
        if dbg_config.get("kpis"):
            print("\nKPIs in Config:")
            for kpi in dbg_config["kpis"]:
                print(f"  - {kpi.get('label')}: value={kpi.get('value')}")
        
        if dbg_config.get("charts"):
            print("\nCharts in Config:")
            for chart in dbg_config["charts"]:
                print(f"  - {chart.get('title')}: data points={len(chart.get('data', []))}")

        # 4. Validation Logic Simulation (Inconsistencies)
        print("\n" + "=" * 20)
        print("INCONSISTENCY CHECK")
        print("=" * 20)
        
        actual_sheets = {s["name"] for s in schema.get("sheets", [])}
        actual_columns_by_sheet = {s["name"]: {c["name"] for c in s.get("columns", [])} for s in schema.get("sheets", [])}
        
        all_actual_cols = set()
        for cols in actual_columns_by_sheet.values():
            all_actual_cols.update(cols)

        # Check KPIs
        for kpi in llm_res.get("kpis", []):
            sheet = kpi.get("sheet")
            formula = kpi.get("formula", "")
            
            if sheet not in actual_sheets:
                print(f"[!] KPI '{kpi.get('label')}' references unknown sheet: {sheet}")
            else:
                import re
                words = re.findall(r"\w+", formula)
                for word in words:
                    # Very basic check: if word is not a common function and not in actual columns
                    if word.upper() not in {"SUM", "AVG", "COUNT", "MIN", "MAX", "MEDIAN"} and \
                       word.lower() not in {c.lower() for c in actual_columns_by_sheet[sheet]}:
                        print(f"[!] KPI '{kpi.get('label')}' references potential hallucination: '{word}' in sheet '{sheet}'")

        # Check Charts
        for chart in llm_res.get("charts", []):
            sheet = chart.get("sheet")
            for axis in ["x_axis", "y_axis", "split_by"]:
                val = chart.get(axis)
                if val:
                    if sheet not in actual_sheets:
                         print(f"[!] Chart '{chart.get('title')}' references unknown sheet: {sheet}")
                         break
                    if val.lower() not in {c.lower() for c in actual_columns_by_sheet[sheet]}:
                        print(f"[!] Chart '{chart.get('title')}' axis '{axis}' references potential hallucination: '{val}' in sheet '{sheet}'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(peek_latest_job())
