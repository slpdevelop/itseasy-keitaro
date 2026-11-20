import { Activity, ArrowDownToLine, ArrowLeft, ArrowUpFromLine, Building2, Check, ChevronDown, ChevronRight, CircleAlert, Database, Globe2, Layers3, LoaderCircle, Plus, RefreshCw, Search, Settings2, ShieldCheck, Trash2, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, getFlowOffers, getFlows, getGeo, getId, getName, getOfferId, getOfferName, normalizeList } from './api';

const fmt = (v) => v == null ? '—' : String(v);
function Toast({toast, onClose}) { if (!toast) return null; return <div className={`toast ${toast.type}`}><span>{toast.type === 'error' ? <CircleAlert size={17}/> : <Check size={17}/>}</span><div>{toast.message}</div><button onClick={onClose}><X size={15}/></button></div>; }
function Modal({children,onClose}) { return <div className="overlay" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><section className="modal">{children}</section></div>; }

export default function App() {
  const [companies,setCompanies] = useState([]);
  const [offers,setOffers] = useState([]);
  const [localOffers,setLocalOffers] = useState([]);
  const [selected,setSelected] = useState(null);
  const [detail,setDetail] = useState(null);
  const [loading,setLoading] = useState(true);
  const [detailLoading,setDetailLoading] = useState(false);
  const [busy,setBusy] = useState('');
  const [query,setQuery] = useState('');
  const [modal,setModal] = useState(false);
  const [toast,setToast] = useState(null);
  const [draft,setDraft] = useState({name:'',geo:'',offerIds:[]});
  const [flowEdits,setFlowEdits] = useState({});
  const [expanded,setExpanded] = useState({});
  const [offerSearch,setOfferSearch] = useState('');

  const notify = (message,type='success') => { setToast({message,type}); window.setTimeout(()=>setToast(null),4500); };
  const loadCompanies = useCallback(async () => {
    setLoading(true);
    try { setCompanies(normalizeList(await api.campaigns())); }
    catch(e) { notify(`Не удалось загрузить компании: ${e.message}`,'error'); }
    finally { setLoading(false); }
  }, []);
  const loadOffers = useCallback(async () => {
    try {
      const [remote,local] = await Promise.all([api.keitaroOffers(),api.localOffers()]);
      setOffers(normalizeList(remote)); setLocalOffers(normalizeList(local));
    } catch(e) { notify(`Не удалось загрузить офферы: ${e.message}`,'error'); }
  }, []);
  useEffect(()=>{ loadCompanies(); loadOffers(); },[loadCompanies,loadOffers]);

  const openCompany = async (company) => {
    const id=getId(company); setSelected(company); setDetail(null); setFlowEdits({}); setDetailLoading(true);
    try { setDetail(await api.campaign(id)); }
    catch(e) { notify(`Не удалось загрузить компанию: ${e.message}`,'error'); }
    finally { setDetailLoading(false); }
  };
  const back = () => { setSelected(null); setDetail(null); setFlowEdits({}); loadCompanies(); };
  const flows = useMemo(()=>getFlows(detail),[detail]);
  const filtered = companies.filter(c => `${getName(c)} ${getGeo(c)} ${getId(c)}`.toLowerCase().includes(query.toLowerCase()));
  const remoteOffer = (id) => offers.find(o => String(getId(o))===String(id) || String(o.keitaro_id)===String(id));
  const isOfferInLocal = (id) => localOffers.some(o=>String(getOfferId(o))===String(id) || String(o.keitaro_id)===String(id));

  const create = async (e) => {
    e.preventDefault();
    if (!draft.name.trim() || !draft.geo.trim()) return;
    setBusy('create');
    try {
      // Keep request mapping in one place: align these keys with KTCampaignCreateRequest if needed.
      const payload={name:draft.name.trim(),country_code:draft.geo.trim().toUpperCase(),offer_id_list:draft.offerIds.map(Number)};
      const result=await api.createCampaign(payload);
      setModal(false); setDraft({name:'',geo:'',offerIds:[]});
      notify(result?.message || 'Компания успешно создана');
      await loadCompanies();
      if (result?.campaign_id) openCompany({id:result.campaign_id,name:result.campaign_name || payload.name,geo:payload.geo});
    } catch(e) { notify(`Ошибка создания: ${e.message}`,'error'); }
    finally { setBusy(''); }
  };
  const toggleDraftOffer = (id) => setDraft(d=>({...d,offerIds:d.offerIds.includes(id)?d.offerIds.filter(x=>x!==id):[...d.offerIds,id]}));
  const getCurrentOffers = (flow) => flowEdits[flow.id] ?? getFlowOffers(flow);
  const changeFlowOffer = (flow,id,add) => {
    const current=getCurrentOffers(flow);
    const next=add
      ? [...current,{offer_id:Number(id),share:100,state:'active'}]
      : current.filter(o=>String(getOfferId(o))!==String(id));
    setFlowEdits(prev=>({...prev,[flow.id]:next}));
  };
  const saveFlow = async (flow) => {
    const next=flowEdits[flow.id]; if (!next) return;
    setBusy(`flow-${flow.id}`);
    try {
      await api.updateFlow({...flow,offers:next});
      setDetail(prev=>({...prev,flows:getFlows(prev).map(f=>f.id===flow.id?{...f,offers:next}:f)}));
      setFlowEdits(prev=>{const n={...prev};delete n[flow.id];return n;});
      notify(`Изменения потока «${flow.name || flow.id}» сохранены`);
    } catch(e) { notify(`Не удалось сохранить поток: ${e.message}`,'error'); }
    finally { setBusy(''); }
  };
  const sync = async (direction) => {
    setBusy(direction);
    try {
      const result=direction==='fetch'?await api.syncFromKeitaro():await api.syncToKeitaro();
      notify(result?.message || (direction==='fetch'?'Данные получены из Keitaro':'Изменения отправлены в Keitaro'));
      if(selected) await openCompany(selected);
      await loadOffers();
    } catch(e) { notify(`Ошибка синхронизации: ${e.message}`,'error'); }
    finally { setBusy(''); }
  };
  const offerPool = offers.filter(o=>!getCurrentOffers({id:'__none__'}).some(()=>false) && `${getOfferName(o)} ${getId(o)}`.toLowerCase().includes(offerSearch.toLowerCase()));

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Layers3 size={20}/></div><div><b>keitaro<span>.</span></b><small>WORKSPACE</small></div></div>
      <div className="side-label">WORKSPACE</div>
      <div className={`nav-item ${!selected?'active':''}`} onClick={back}><Building2 size={17}/> Companies <span className="nav-count">{companies.length}</span></div>
      <div className="side-bottom"><div className="connection"><span className="pulse"></span><div><b>API connection</b><small>Backend endpoint</small></div><ShieldCheck size={16}/></div><div className="profile"><div className="avatar">AD</div><div><b>Admin</b><small>Workspace</small></div><Settings2 size={17}/></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb"><span>Workspace</span><ChevronRight size={14}/><b>{selected?getName(selected):'Companies'}</b></div><div className="top-actions"><span className="live-dot"></span><span>Keitaro integration</span><button className="icon-btn" title="Refresh" onClick={()=>selected?openCompany(selected):(loadCompanies(),loadOffers())}><RefreshCw size={16}/></button></div></header>
      {!selected ? <section className="content">
        <div className="page-heading"><div><div className="eyebrow">OVERVIEW / COMPANIES</div><h1>Companies</h1><p>Управляйте компаниями, потоками и привязками офферов.</p></div><button className="primary-btn" onClick={()=>setModal(true)}><Plus size={17}/> Новая компания</button></div>
        <div className="section-head"><div><h2>Список компаний</h2><p>Выберите компанию, чтобы открыть потоки и офферы</p></div><div className="searchbox"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Поиск компании..."/></div></div>
        <div className="table-card"><div className="table-header"><span>КОМПАНИЯ</span><span>GEO</span><span>ID</span><span>СТАТУС</span><span></span></div>
          {loading?<div className="empty"><LoaderCircle className="spin" size={22}/>Загружаем компании...</div>:filtered.length===0?<div className="empty"><Building2 size={24}/><b>Компании не найдены</b><span>Создайте новую компанию или измените поисковый запрос.</span></div>:filtered.map(c=><button className="company-row" key={getId(c)} onClick={()=>openCompany(c)}><div className="company-name"><div className="company-icon"><Building2 size={17}/></div><div><b>{getName(c)}</b><small>Campaign workspace</small></div></div><span className="geo-pill"><Globe2 size={13}/>{getGeo(c)}</span><span className="muted mono">#{getId(c)}</span><span><i className="status-dot"></i><span className="status-text">Active</span></span><ChevronRight size={17} className="row-arrow"/></button>)}
        </div>
        <div className="footnote">Показано {filtered.length} из {companies.length} компаний</div>
      </section> : <section className="content detail-content">
        <button className="back-link" onClick={back}><ArrowLeft size={16}/> Все компании</button>
        <div className="page-heading detail-heading"><div><div className="eyebrow">COMPANY / DETAILS</div><h1>{getName(detail || selected)}</h1><p>Настройка потоков и управление офферами компании.</p></div><div className="sync-actions"><button className="secondary-btn" disabled={!!busy} onClick={()=>sync('fetch')}>{busy==='fetch'?<LoaderCircle className="spin" size={16}/>:<ArrowDownToLine size={16}/>} Fetch from Keitaro</button><button className="primary-btn" disabled={!!busy} onClick={()=>sync('sync')}>{busy==='sync'?<LoaderCircle className="spin" size={16}/>:<ArrowUpFromLine size={16}/>} Sync to Keitaro</button></div></div>
        <div className="company-summary"><div className="summary-icon"><Building2 size={22}/></div><div className="summary-main"><small>COMPANY</small><b>{getName(detail || selected)}</b><span className="muted">ID: {fmt(getId(detail || selected))}</span></div><div className="summary-divider"></div><div className="summary-meta"><small>GEO CODE</small><b><Globe2 size={14}/>{getGeo(detail || selected)}</b></div><div className="summary-divider"></div><div className="summary-meta"><small>FLOWS</small><b><Layers3 size={14}/>{detailLoading?'…':flows.length}</b></div></div>
        <div className="section-head flows-head"><div><h2>Company flows</h2><p>Потоки компании и назначенные на них офферы</p></div><span className="count-chip">{flows.length} flows</span></div>
        {detailLoading?<div className="empty"><LoaderCircle className="spin" size={22}/>Загружаем потоки...</div>:flows.length===0?<div className="empty panel-empty"><Layers3 size={25}/><b>Потоки не найдены</b><span>Для этой компании пока нет потоков.</span></div>:<div className="flows-list">{flows.map((flow,index)=>{
          const current=getCurrentOffers(flow), changed=!!flowEdits[flow.id], flowId=flow.id ?? flow.stream_id ?? index;
          const boundIds=current.map(getOfferId).filter(x=>x!=null).map(String);
          const available=offers.filter(o=>!boundIds.includes(String(getId(o)))&&!boundIds.includes(String(o.keitaro_id)));
          return <article className="flow-card" key={flowId}>
            <div className="flow-top" onClick={()=>setExpanded(p=>({...p,[flowId]:!p[flowId]}))}><div className="flow-type-icon"><Layers3 size={18}/></div><div className="flow-title"><div><b>{flow.name || `Flow ${flowId}`}</b><span className="flow-id">ID #{flowId}</span></div><small>{flow.type || flow.schema || 'Regular flow'} · {flow.state || 'Active'}</small></div><div className="flow-offer-count">{current.length} {current.length===1?'offer':'offers'}</div>{changed&&<span className="pending-tag">Unsaved</span>}<button className="expand-btn" aria-label="Toggle flow"><ChevronDown className={expanded[flowId]===false?'collapsed':''} size={18}/></button></div>
            {expanded[flowId]!==false&&<div className="flow-body">
              {current.length===0?<div className="no-offers"><div className="no-offer-icon"><Database size={16}/></div><div><b>Офферы не назначены</b><span>Этот поток пока не содержит офферов.</span></div></div>:<div className="offer-list">{current.map((o,i)=>{const id=getOfferId(o);const remote=remoteOffer(id);return <div className="offer-row" key={`${id}-${i}`}><div className="offer-symbol">O</div><div className="offer-info"><b>{getOfferName({...remote,...o})}</b><small>Keitaro ID: {fmt(id)}</small></div><span className="share">{o.share ?? 100}% share</span><span className={`sync-tag ${o.synced===false?'unsynced':''}`}>{o.synced===false?'Pending sync':'Linked'}</span><button className="remove-btn" title="Удалить оффер из потока" onClick={()=>changeFlowOffer(flow,id,false)}><Trash2 size={15}/></button></div>})}</div>}
              <div className="flow-controls"><div className="add-offer"><select value="" onChange={e=>e.target.value&&changeFlowOffer(flow,e.target.value,true)}><option value="">+ Добавить оффер из Keitaro</option>{available.map(o=><option key={getId(o)} value={getId(o)}>{getOfferName(o)} · #{getId(o)}</option>)}</select><ChevronDown size={14}/></div><button className="save-btn" disabled={!changed||busy===`flow-${flow.id}`} onClick={()=>saveFlow(flow)}>{busy===`flow-${flow.id}`?<LoaderCircle className="spin" size={14}/>:<Check size={14}/>} Сохранить изменения</button></div>
              <div className="flow-foot"><span>Stream ID: {flowId}</span><span>{changed?'Изменения ожидают сохранения':'Состояние потока актуально'}</span></div>
            </div>}
          </article>
        })}</div>}
        <div className="sync-note"><div><ShieldCheck size={17}/></div><p><b>Синхронизация в два направления</b><br/>Fetch загружает привязки офферов из Keitaro в локальную БД. Sync отправляет локальные изменения привязок обратно в Keitaro.</p></div>
      </section>}
    </main>
    {modal&&<Modal onClose={()=>setModal(false)}><div className="modal-head"><div><div className="eyebrow">NEW WORKSPACE</div><h2>Создать компанию</h2><p>Укажите название, GEO и офферы для новой компании.</p></div><button className="icon-btn" onClick={()=>setModal(false)}><X size={18}/></button></div><form onSubmit={create}><label>Название компании<input required autoFocus placeholder="Например, test_company_eu" value={draft.name} onChange={e=>setDraft(d=>({...d,name:e.target.value}))}/></label><label>GEO код<input required maxLength="3" placeholder="DE" value={draft.geo} onChange={e=>setDraft(d=>({...d,geo:e.target.value.toUpperCase()}))}/><small>Двухбуквенный код страны, например DE, US, FR</small></label><label>Офферы <span className="optional">необязательно</span></label><div className="offer-picker"><div className="picker-search"><Search size={15}/><input placeholder="Найти оффер..." value={offerSearch} onChange={e=>setOfferSearch(e.target.value)}/></div><div className="picker-options">{offers.filter(o=>`${getOfferName(o)} ${getId(o)}`.toLowerCase().includes(offerSearch.toLowerCase())).map(o=><label className="picker-option" key={getId(o)}><input type="checkbox" checked={draft.offerIds.includes(getId(o))} onChange={()=>toggleDraftOffer(getId(o))}/><span><b>{getOfferName(o)}</b><small>ID: {getId(o)}</small></span></label>)}{offers.length===0&&<div className="picker-empty">Офферы не загружены</div>}</div></div>{draft.offerIds.length>0&&<div className="selected-count">{draft.offerIds.length} оффер(ов) выбрано</div>}<div className="modal-actions"><button type="button" className="secondary-btn" onClick={()=>setModal(false)}>Отмена</button><button className="primary-btn" disabled={busy==='create'}>{busy==='create'?<LoaderCircle className="spin" size={16}/>:<Plus size={16}/>} Создать компанию</button></div></form></Modal>}
    <Toast toast={toast} onClose={()=>setToast(null)}/>
  </div>;
}