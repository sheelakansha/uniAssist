import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './styles.css';

// Same-origin proxy works whether the dashboard is opened via localhost or
// Vite's network address; Vite forwards /api to FastAPI.
const API='/api';

const prompts=["What is S1001's attendance in CS201?", "Is S1001 eligible for CS201?", "What are S1001's backlogs?", "What is CS201?"];
const Panel=({title,children,open=false}) => <details className="panel" open={open}><summary>{title}<span>⌄</span></summary><div className="panel-body">{children}</div></details>;
const Json=({data}) => { try { return <pre>{JSON.stringify(data ?? {},null,2)}</pre> } catch { return <pre>Evidence could not be rendered safely.</pre> } };
class ErrorBoundary extends React.Component {
  constructor(props){super(props);this.state={error:null}}
  static getDerivedStateFromError(error){return {error}}
  render(){return this.state.error?<main style={{padding:40,color:'#e9eef8',background:'#07111f',minHeight:'100vh',fontFamily:'system-ui'}}><h2>Dashboard recovered from a display error</h2><p>The backend is still running. Refresh the page to retry.</p><pre style={{whiteSpace:'pre-wrap',color:'#f2c661'}}>{this.state.error.message}</pre></main>:this.props.children}
}
function AssistantMessage({data}){
  const safe=data && typeof data==='object' ? data : {answer:'The service returned an unexpected response.', raw:data};
  const citations=Array.isArray(safe.citations)?safe.citations:[];
  return <div className="message assistant"><span>NSUT Assistant</span><p>{typeof safe.answer==='string'?safe.answer:'No verified answer was returned.'}</p>
    {safe.decision&&<Panel title="Decision" open><Json data={safe.decision}/></Panel>}
    <div className="grid">{safe.evidence&&<Panel title="Evidence"><Json data={safe.evidence}/></Panel>}{citations.length>0&&<Panel title="Citations"><Json data={citations}/></Panel>}{safe.audit&&<Panel title="Audit trail"><Json data={safe.audit}/></Panel>}{safe.error&&<Panel title="Service detail"><Json data={safe.error}/></Panel>}</div>
  </div>
}

function App(){
  const [studentId,setStudentId]=useState('S1001');
  const [query,setQuery]=useState('');
  const [messages,setMessages]=useState([]);
  const [health,setHealth]=useState('checking');
  const [sending,setSending]=useState(false);
  useEffect(()=>{fetch(`${API}/health`).then(r=>r.ok?r.json():Promise.reject()).then(()=>setHealth('online')).catch(()=>setHealth('offline'))},[]);
  async function ask(value=query){
    const text=value.trim(); if(!text||sending)return;
    setMessages(m=>[...m,{role:'user',text}]); setQuery(''); setSending(true);
    try { const r=await fetch(`${API}/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:text,student_id:studentId||null})});
      const data=await r.json().catch(()=>({answer:'The backend returned an invalid response.'})); if(!r.ok)throw new Error(data.detail||'Backend request failed'); setMessages(m=>[...m,{role:'assistant',data}]);
    } catch(error){setMessages(m=>[...m,{role:'assistant',data:{answer:'The backend could not be reached. Start FastAPI on port 8000.',error:error.message}}])} finally {setSending(false)}
  }
  return <main className="shell">
    <aside className="sidebar"><div className="brand"><div className="crest">N</div><div><b>NSUT</b><small>Academic Intelligence Desk</small></div></div>
      <section><p className="eyebrow">STUDENT CONTEXT</p><label>Student ID<input value={studentId} onChange={e=>setStudentId(e.target.value.toUpperCase())} placeholder="S1001" maxLength="5"/></label><p className="hint">Student data is queried only from the local academic database.</p></section>
      <section className="status"><span className={'dot '+health}/><div><b>System {health}</b><small>FastAPI + verified sources</small></div></section>
      <section className="guardrail"><p className="eyebrow">GROUNDING</p><p>Student facts come from SQLite. Policy answers require an active, registered official document.</p></section>
      <footer>NSUT AI Assistant<br/><small>Traceable · Private · Deterministic</small></footer>
    </aside>
    <section className="workspace"><header><div><p className="eyebrow">LIVE ASSISTANT</p><h1>Academic support with evidence.</h1></div><span className="badge">Verified workflow</span></header>
      <div className="conversation">{messages.length===0&&<div className="welcome"><div className="spark">✦</div><h2>How can I help today?</h2><p>Ask about your student record, attendance, results, backlogs, courses, or an indexed official policy.</p><div className="suggestions">{prompts.map(p=><button key={p} onClick={()=>ask(p)}>{p}</button>)}</div></div>}
      {messages.map((m,i)=>m.role==='user'?<div key={i} className="message user"><span>You</span><p>{m.text}</p></div>:<AssistantMessage key={i} data={m.data}/>)}{sending&&<div className="typing">Checking verified sources<span>•••</span></div>}</div>
      <form className="composer" onSubmit={e=>{e.preventDefault();ask()}}><textarea value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ask a verified academic question…" rows="2"/><button disabled={sending||!query.trim()}>{sending?'Working…':'Send ↗'}</button></form>
    </section>
  </main>
}
createRoot(document.getElementById('root')).render(<ErrorBoundary><App/></ErrorBoundary>);
