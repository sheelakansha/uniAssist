"""Register an administrator-reviewed local NSUT document for ingestion.

Example:
python scripts/register_source.py --id nsut-reg-2026 --file real_corpus/regulations/regulations.pdf --title "NSUT B.Tech Regulations 2026" --category regulations --authority 100
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import ROOT

p=argparse.ArgumentParser()
p.add_argument('--id',required=True); p.add_argument('--file',required=True); p.add_argument('--title',required=True)
p.add_argument('--category',required=True,choices=['regulations','policy','academic_calendar','fees','curriculum','notice'])
p.add_argument('--authority',type=int,required=True); p.add_argument('--poll-minutes',type=int,default=1440)
a=p.parse_args(); path=(ROOT/a.file).resolve()
if not path.is_file() or ROOT not in path.parents: p.error('--file must be an existing file inside this project')
registry=ROOT/'runtime'/'sources.json'; registry.parent.mkdir(parents=True,exist_ok=True)
sources=json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else []
if any(x['source_id']==a.id for x in sources): p.error('source id already exists')
sources.append({'source_id':a.id,'name':a.title,'source_type':'local_file','source_uri':str(path),'category':a.category,'authority_level':a.authority,'enabled':True,'poll_minutes':a.poll_minutes})
registry.write_text(json.dumps(sources,indent=2),encoding='utf-8')
print(f'Registered {a.id}; run python scripts/ingest.py')
