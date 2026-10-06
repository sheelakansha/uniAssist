"""Offline routing/evidence smoke evaluation; never manufactures expected answers."""
import json
from pathlib import Path
from app.service import service

questions=json.loads((Path(__file__).parent/'questions.json').read_text(encoding='utf-8'))
correct=0; results=[]
for item in questions:
    result=service.chat(item['question'])
    ok=result['intent']==item['expected_intent']; correct+=ok
    results.append({'question':item['question'],'expected_intent':item['expected_intent'],'actual_intent':result['intent'],'passed':ok})
report={'total':len(results),'intent_accuracy':correct/len(results),'results':results}
(Path(__file__).parent/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'total':report['total'],'intent_accuracy':report['intent_accuracy']}))
