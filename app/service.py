import time, uuid
from typing import Any
from app.config import settings
from app.db_registry import Registry
from ingestion.engine import IngestionEngine
from rag.policy_engine import PolicyEngine
from graph.router import route_query
from tools.student import get_student
from tools.attendance import get_attendance
from tools.results import get_results
from tools.backlog import get_backlogs
from tools.course import get_course
from tools.eligibility import check_attendance_threshold
from llm.local_llm import LocalLLM

class AssistantService:
    def __init__(self):
        self.registry=Registry(settings.registry_path); self.ingestion=IngestionEngine(self.registry); self.policy=PolicyEngine(self.registry)
    def ensure_knowledge(self):
        # Chat requests must never trigger extraction, model downloads, or
        # embedding work. Ingestion is an explicit admin operation only.
        return None
    def has_active_policy(self) -> bool:
        return bool(self.registry.documents(active_only=True))
    def chat(self, query: str, student_id: str | None=None) -> dict[str, Any]:
        started=time.perf_counter(); request_id=str(uuid.uuid4()); route=route_query(query)
        if student_id: route['student_id']=student_id.upper()
        intent=route['intent']; sid=route.get('student_id'); course=route.get('course_code'); tools=[]; evidence={}; decision=None; policy_docs=[]; error=None
        needs_student={"attendance","attendance_eligibility","results","backlogs","student"}
        if intent in needs_student and not sid: error="Please provide a student ID, for example S1001."
        elif intent=="student": tools.append("get_student"); evidence['student_facts']=get_student(sid)
        elif intent=="attendance": tools.append("get_attendance"); evidence['database_results']=get_attendance(sid,course)
        elif intent=="results": tools.append("get_results"); evidence['database_results']=get_results(sid,course)
        elif intent=="backlogs": tools.append("get_backlogs"); evidence['database_results']=get_backlogs(sid)
        elif intent=="course":
            if not course: error="Please provide a course code, for example CS201."
            else: tools.append("get_course"); evidence['database_results']=get_course(course)
        elif intent=="attendance_eligibility":
            if not course: error="Please provide a course code, for example CS201."
            else:
                self.ensure_knowledge()
                if not self.has_active_policy(): error="I could not find an active authoritative NSUT policy for this question. Register and ingest an official NSUT document first."
                else:
                    rule,policy_docs,reason=self.policy.resolve("minimum attendance examination eligibility", "attendance_minimum")
                    if not rule: error="I could not find an active authoritative NSUT policy for this question."
                    else:
                        tools.append("check_attendance_threshold"); decision=check_attendance_threshold(sid,course,rule['required_percentage']); evidence['policy_rules']=[rule]; evidence['database_results']=decision
        elif intent in {"university_policy","degree_requirement","promotion","examination","academic_calendar","fees","syllabus"}:
            self.ensure_knowledge()
            if not self.has_active_policy(): error="I could not find an active authoritative NSUT policy for this question. Register and ingest an official NSUT document first."
            else:
                policy_docs=self.policy.retrieve(query)
                if "attendance" in query.lower():
                    rule,resolved_docs,_=self.policy.resolve(query,"attendance_minimum")
                    if rule:
                        evidence['policy_rules']=[rule]
                        policy_docs=resolved_docs
            if not error and not policy_docs: error="I could not find an active authoritative NSUT policy for this question."
            else: evidence['policy_evidence']=[self._citation(d) | {'excerpt': self._excerpt(d['text'],query)} for d in policy_docs]
        else: error="I don't have verified information for that."
        citations=[self._citation(d) for d in policy_docs]
        answer=self._answer(query,intent,evidence,decision,error,citations)
        latency=round((time.perf_counter()-started)*1000)
        audit={"request_id":request_id,"intent":intent,"tools_used":tools,"documents_retrieved":[d['document_id'] for d in policy_docs],"decision":decision,"model":settings.llm_model if settings.llm_mode!='mock' else 'mock',"latency_ms":latency,"llm_status":"mock" if settings.llm_mode=='mock' else 'not_invoked'}
        # Preserve only routing/operational metadata, not the raw student question.
        self.registry.record_audit(audit)
        return {"request_id":request_id,"answer":answer,"intent":intent,"decision":decision,"evidence":evidence,"sources":citations,"citations":citations,"audit":audit,"error":error}
    def _answer(self,q,intent,evidence,decision,error,citations):
        if error: return error
        if decision:
            status="ELIGIBLE" if decision.get('meets_threshold') else "NOT ELIGIBLE"
            return f"{decision['student_id']}'s attendance in {decision['course_code']} is {decision['actual_percentage']}%. The retrieved active policy requires {decision['required_percentage']}%. Eligibility: {status}."
        data=evidence.get('database_results') or evidence.get('student_facts')
        if data:
            if data.get('found') is False: return data.get('message') or "No verified record was found."
            if intent=='attendance': return f"Verified attendance records: {data.get('attendance', [])}"
            if intent=='backlogs': return f"Active backlogs: {data.get('active_backlogs')}. Records: {data.get('backlogs', [])}"
            return f"Verified database result: {data}"
        policy=evidence.get('policy_evidence',[])
        rules=evidence.get('policy_rules',[])
        if rules and rules[0].get('rule_type')=='attendance_minimum':
            return f"The active retrieved regulation requires a minimum attendance of {rules[0]['required_percentage']}% for examination eligibility." + (f" Source: {citations[0]['title']}." if citations else "")
        return (policy[0]['excerpt'] if policy else "I don't have verified information for that.") + (f" Source: {citations[0]['title']}." if citations else "")
    @staticmethod
    def _excerpt(text,q):
        terms=[x.lower() for x in q.split() if len(x)>3]; pos=min([text.lower().find(t) for t in terms if text.lower().find(t)>=0] or [0]); return " ".join(text[max(0,pos-180):pos+650].split())
    @staticmethod
    def _citation(d): return {"document_id":d['document_id'],"source_id":d['source_id'],"title":d['title'],"version":d.get('version_label'),"authority_level":d['authority_level'],"effective_from":d.get('effective_from'),"source_uri":d.get('source_uri')}

service=AssistantService()
