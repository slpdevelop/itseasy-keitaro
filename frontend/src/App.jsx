import { Activity, ArrowDownToLine, ArrowLeft, ArrowUpFromLine, Building2, Check, ChevronDown, ChevronRight, CircleAlert, Database, Globe2, Layers3, LoaderCircle, Plus, RefreshCw, Search, Settings2, ShieldCheck, Trash2, X, Pin, PinOff } from 'lucide-react';
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
    const id=getId(company); setSelected(company); setDetail(null); setDetailLoading(true);
    try { setDetail(await api.campaign(id)); }
    catch(e) { notify(`Не удалось загрузить компанию: ${e.message}`,'error'); }
    finally { setDetailLoading(false); }
  };
  const back = () => { setSelected(null); setDetail(null); loadCompanies(); };
  const flows = useMemo(()=>getFlows(detail),[detail]);
  const isGeoFlow = (flow) => flow?.type === 'GEO' || flow?.type === 'geo';
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
  const getCurrentOffers = (flow) => getFlowOffers(flow);
  const isDeletedOffer = (offer) => offer?.deleted === true || offer?.is_deleted === true || String(offer?.state ?? '').toLowerCase() === 'deleted';
  const recalculateShares = (items) => {
    const active = items.filter(item => !isDeletedOffer(item));
    const pinned = active.filter(item => item.pinned);
    const unpinned = active.filter(item => !item.pinned);
    const pinnedTotal = pinned.reduce((sum, item) => sum + Number(item.share || 0), 0);
    if (pinnedTotal > 100) throw new Error('Сумма закреплённых Share не может превышать 100%');
    const remaining = 100 - pinnedTotal;
    if (!unpinned.length && active.length && remaining !== 0) {
      throw new Error('Все офферы закреплены: их Share должны в сумме составлять 100%');
    }
    const base = unpinned.length ? Math.floor(remaining / unpinned.length) : 0;
    const remainder = unpinned.length ? remaining % unpinned.length : 0;
    const remainderStart = unpinned.length - remainder;
    let unpinnedIndex = 0;
    return items.map(item => {
      if (isDeletedOffer(item)) return {...item, share: 0, pinned: false};
      if (item.pinned) return {...item, share: Number(item.share || 0)};
      const share = base + (unpinnedIndex >= remainderStart ? 1 : 0);
      unpinnedIndex += 1;
      return {...item, share};
    });
  };
  const changeFlowOffer = async (flow,id,action,value) => {
    const flowId = flow.id ?? flow.stream_id;
    if (busy === `flow-${flowId}`) return;
    const current = getCurrentOffers(flow);
    let next;
    if (action === 'add') {
      // Existing bindings (including soft-deleted ones) cannot be added twice.
      if (current.some(item => String(getOfferId(item)) === String(id))) return;
      next = [...current,{offer_id:Number(id),share:0,state:'active',deleted:false}];
    } else {
      next = current.map(item => {
        if (String(getOfferId(item)) !== String(id)) return item;
        if (action === 'restore') return {...item,state:'active',deleted:false};
        if (action === 'delete') return {...item,state:'deleted',deleted:true,pinned:false};
        if (action === 'pin') return {...item,pinned:true};
        if (action === 'unpin') return {...item,pinned:false};
        if (action === 'share') return {...item,share:Number(value),pinned:true};
        return item;
      });
    }
    try { next = recalculateShares(next); }
    catch(e) { notify(e.message,'error'); return; }
    setBusy(`flow-${flowId}`);
    try {
      await api.updateFlow({...flow,id:flowId,offers:next});
      setDetail(prev => {
        if (!prev) return prev;
        const updated = getFlows(prev).map(item => (item.id ?? item.stream_id) === flowId ? {...item,offers:next} : item);
        return {...prev,flows:updated,streams:prev.streams ? updated : prev.streams};
      });
      notify(action === 'add' ? 'Оффер добавлен' : action === 'restore' ? 'Оффер восстановлен' : action === 'delete' ? 'Оффер помечен удалённым' : action === 'pin' ? 'Share закреплён' : action === 'unpin' ? 'Share откреплён' : 'Share обновлён');
    } catch(e) {
      notify(`Не удалось обновить офферы потока: ${e.message}`,'error');
    } finally {
      setBusy('');
    }
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
      <div className="side-bottom"><div className="connection"><span className="pulse"></span><div><b>API connection</b><small>Backend endpoint</small></div><ShieldCheck size={16}/></div></div>
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
          const current=getCurrentOffers(flow), flowId=flow.id ?? flow.stream_id ?? index;
          const boundIds=current.map(getOfferId).filter(x=>x!=null).map(String);
          const available=offers.filter(o=>!boundIds.includes(String(getId(o)))&&!boundIds.includes(String(o.keitaro_id)));
          const hideBody = isGeoFlow(flow);
          return <article className="flow-card" key={flowId}>
            <div className="flow-top" onClick={()=>setExpanded(p=>({...p,[flowId]:!p[flowId]}))}><div className="flow-type-icon"><Layers3 size={18}/></div><div className="flow-title"><div><b>{flow.name || `Flow ${flowId}`}</b><span className="flow-id">ID #{flowId}</span></div><small>{flow.type || flow.schema || 'Regular flow'} · {flow.state || 'Active'}</small></div><div className="flow-offer-count">{current.length} {current.length===1?'offer':'offers'}</div><button className="expand-btn" aria-label="Toggle flow"><ChevronDown className={expanded[flowId]===false?'collapsed':''} size={18}/></button></div>
            {expanded[flowId]!==false&&hideBody==false&&<div className="flow-body">
              {current.length===0?<div className="no-offers"><div className="no-offer-icon"><Database size={16}/></div><div><b>Офферы не назначены</b><span>Этот поток пока не содержит офферов.</span></div></div>:<div className="offer-list">{current.map((o,i)=>{const id=getOfferId(o);const remote=remoteOffer(id);const deleted=isDeletedOffer(o);return <div className={`offer-row ${deleted?'offer-row-deleted':''}`} key={`${id}-${i}`}><div className="offer-symbol">O</div><div className="offer-info"><b>{getOfferName({...remote,...o})}</b><small>Keitaro ID: {fmt(id)}{deleted?' · Удалён':''}</small></div><div className="share-editor"><input aria-label="Share percentage" type="number" min="0" max="100" step="1" defaultValue={o.share ?? 0} disabled={deleted || busy===`flow-${flowId}`} onBlur={e=>{const value=Number(e.target.value);if(Number.isInteger(value)&&value>=0&&value<=100&&value!==Number(o.share))changeFlowOffer(flow,id,'share',value);else e.target.value=String(o.share ?? 0);}}/><span>%</span></div>{!deleted&&<button className={`pin-btn ${o.pinned?'pinned':''}`} title={o.pinned?'Открепить Share':'Закрепить Share'} disabled={busy===`flow-${flowId}`} onClick={()=>changeFlowOffer(flow,id,o.pinned?'unpin':'pin')}>{o.pinned?<Pin size={14}/>:<PinOff size={14}/>}</button>}<span className={`sync-tag ${o.synced===false?'unsynced':''}`}>{o.synced===false?'Pending sync':'Linked'}</span>{deleted?<button className="restore-btn" title="Восстановить оффер" disabled={busy===`flow-${flowId}`} onClick={()=>changeFlowOffer(flow,id,'restore')}><RefreshCw size={14}/> Restore</button>:<button className="remove-btn" title="Пометить оффер удалённым" disabled={busy===`flow-${flowId}`} onClick={()=>changeFlowOffer(flow,id,'delete')}><Trash2 size={15}/></button>}</div>})}</div>}
              <div className="flow-controls"><div className="add-offer"><select value="" disabled={busy===`flow-${flowId}`} onChange={e=>e.target.value&&changeFlowOffer(flow,e.target.value,'add')}><option value="">+ Добавить оффер из Keitaro</option>{available.map(o=><option key={getId(o)} value={getId(o)}>{getOfferName(o)} · #{getId(o)}</option>)}</select><ChevronDown size={14}/></div>{busy===`flow-${flowId}`&&<span className="saving-indicator"><LoaderCircle className="spin" size={14}/> Сохранение…</span>}</div>
              <div className="flow-foot"><span>Stream ID: {flowId}</span><span>Изменения сохраняются автоматически</span></div>
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