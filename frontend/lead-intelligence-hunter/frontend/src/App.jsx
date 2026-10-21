import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity, AlertCircle, ArrowUpRight, BookOpen, Check, CheckCheck, ChevronDown, ChevronLeft,
  ChevronRight, CircleHelp, ClipboardList, Code2, Database, ExternalLink, FileText, Filter,
  Github, Globe, Layers3, LayoutDashboard, LoaderCircle, Menu, MoreHorizontal, Plus, RefreshCw,
  Search, Settings2, SlidersHorizontal, Sparkles, Trash2, Users, X, Zap,
} from 'lucide-react'
import { asArray, del, get, getApiBaseUrl, post, put } from './api.js'

const NAV = [
  { section: 'Рабочее пространство' },
  { id: 'dashboard', label: 'Обзор', icon: LayoutDashboard },
  { id: 'leads', label: 'Лиды', icon: Zap },
  { id: 'profiles', label: 'Профили специалистов', icon: Users },
  { id: 'notes', label: 'Заметки и задачи', icon: ClipboardList },
  { section: 'GitHub intelligence' },
  { id: 'repositories', label: 'Репозитории и issues', icon: Github },
  { id: 'matching', label: 'Подбор профилей', icon: Layers3 },
  { id: 'training', label: 'Обучающие примеры', icon: BookOpen },
  { id: 'finded', label: 'Найденные признаки', icon: Search },
  { section: 'Система' },
  { id: 'settings', label: 'LLM и настройки', icon: Settings2 },
]

const PAGE_META = {
  dashboard: ['Обзор', 'Сводка по лидам, специалистам и результатам анализа.'],
  leads: ['Лиды', 'Единый список потенциальных клиентов из подключённых источников.'],
  profiles: ['Профили специалистов', 'Навыки команды, опыт и направления, которые можно закрыть.'],
  notes: ['Заметки и задачи', 'Контекст работы с лидами и следующие действия.'],
  repositories: ['GitHub intelligence', 'Репозитории, issues, комментарии и результаты LLM-анализа.'],
  matching: ['Подбор профилей', 'Результаты сопоставления GitHub issues со специалистами.'],
  training: ['Обучающие примеры', 'Данные, которые используются для последующего обучения и оценки.'],
  finded: ['Найденные признаки', 'Сохранённые группы и поисковые признаки коллектора.'],
  settings: ['LLM и настройки', 'Выбор провайдера модели и просмотр настроек приложения.'],
}

const EMPTY_DATA = {
  leads: [], profiles: [], notes: [], repositories: [], matching: [], training: [], finded: [], settings: [],
  provider: null, health: null, stats: null,
}

function titleCase(value) {
  return String(value ?? '').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase())
}
function showValue(value, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
function percent(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (!Number.isFinite(num)) return String(value)
  return `${Math.round(num * 100)}%`
}
function shortText(value, size = 140) {
  const text = String(value || '')
  return text.length > size ? `${text.slice(0, size).trim()}…` : text
}
function objectCount(value, key) {
  if (Array.isArray(value)) return value.length
  if (value && typeof value === 'object') return Number(value[key] ?? 0)
  return 0
}
function getIdList(value) {
  if (!Array.isArray(value)) return []
  return value.map(x => typeof x === 'object' ? x.id : x).filter(x => x !== undefined && x !== null).map(Number)
}

function Button({ children, onClick, variant = 'primary', size = '', disabled = false, type = 'button', icon: Icon, title }) {
  return <button type={type} title={title} className={`btn ${variant} ${size}`} onClick={onClick} disabled={disabled}>
    {Icon && <Icon size={15} strokeWidth={2} />}{children}
  </button>
}
function IconButton({ icon: Icon, onClick, title, danger = false, disabled = false }) {
  return <button className={`icon-btn ${danger ? 'danger' : ''}`} onClick={onClick} title={title} aria-label={title} disabled={disabled}><Icon size={16} /></button>
}
function Badge({ children, tone = 'neutral' }) { return <span className={`badge ${tone}`}>{children}</span> }
function EmptyState({ icon: Icon = CircleHelp, title = 'Здесь пока пусто', children }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={22} /></span><strong>{title}</strong><span>{children}</span></div>
}
function LoadingState() { return <div className="loading-state"><LoaderCircle className="spin" size={22} /> Загружаем данные…</div> }
function Score({ value }) {
  if (value === null || value === undefined || value === '') return <span className="muted">—</span>
  const n = Number(value)
  return <span className="score"><span className="score-track"><span style={{ width: `${Math.max(0, Math.min(100, n * 100))}%` }} /></span><b>{percent(n)}</b></span>
}
function Panel({ title, subtitle, action, children, className = '' }) {
  return <section className={`panel ${className}`}><div className="panel-head"><div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section>
}
function SearchBox({ value, onChange, placeholder = 'Поиск…' }) {
  return <label className="search-box"><Search size={16} /><input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} /><kbd>/</kbd></label>
}
function PageHeading({ page, right }) {
  const meta = PAGE_META[page] || ['Панель', '']
  return <div className="page-heading"><div><div className="eyebrow">LEAD INTELLIGENCE HUNTER <span className="eyebrow-dot" /></div><h1>{meta[0]}</h1><p>{meta[1]}</p></div>{right}</div>
}
function MetricCard({ label, value, helper, icon: Icon, tone = 'mint' }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={18} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-helper">{helper}</div></div>
}
function StatusDot({ online }) { return <span className={`status-dot ${online ? 'online' : 'offline'}`} /> }

const MODAL_FIELDS = {
  lead: [
    { key: 'source', label: 'Источник', required: true, placeholder: 'reddit, github, upwork…' },
    { key: 'source_id', label: 'ID источника', required: true, placeholder: 'reddit_123' },
    { key: 'title', label: 'Заголовок', placeholder: 'Короткая суть лида' },
    { key: 'url', label: 'URL', required: true, placeholder: 'https://…' },
    { key: 'author', label: 'Автор / аккаунт', placeholder: 'username' },
    { key: 'score', label: 'Оценка релевантности (0–1)', type: 'number', min: 0, max: 1, step: 0.01 },
    { key: 'group', label: 'Группа', placeholder: 'например, web-dev' },
    { key: 'text', label: 'Описание / текст', type: 'textarea', required: true, wide: true },
  ],
  profile: [
    { key: 'description', label: 'Описание специалиста', type: 'textarea', required: true, wide: true },
    { key: 'stack', label: 'Технологии / stack', type: 'textarea', placeholder: 'Python, Flask, PostgreSQL…', wide: true },
    { key: 'experience', label: 'Опыт', placeholder: '3 года, Senior…' },
    { key: 'can_solve', label: 'Какие задачи решает', type: 'textarea', wide: true },
    { key: 'url_resume', label: 'Резюме', placeholder: 'https://…' },
    { key: 'portfolio', label: 'Портфолио / GitHub', placeholder: 'https://…' },
    { key: 'success_score', label: 'Коэффициент успеха (0–1)', type: 'number', min: 0, max: 1, step: 0.01, required: true },
  ],
  note: [
    { key: 'text', label: 'Текст заметки / задачи', type: 'textarea', required: true, wide: true },
    { key: 'purpose', label: 'Цель / следующий шаг', type: 'textarea', required: true, wide: true },
  ],
}

function RecordModal({ modal, onClose, onSave, profiles, leads, saving }) {
  const [form, setForm] = useState({})
  const [selectedLeadIds, setSelectedLeadIds] = useState([])
  const [filterLeads, setFilterLeads] = useState('')

  useEffect(() => {
    if (!modal) return
    const item = modal.item || {}
    const initial = {}
    const fields = MODAL_FIELDS[modal.type] || []
    fields.forEach(field => {
      initial[field.key] = item[field.key] ?? (field.key === 'success_score' ? 0 : field.key === 'score' ? '' : '')
    })
    if (modal.type === 'note') {
      initial.profile_id = item.profile_id ?? item.profile ?? (profiles[0]?.id ?? '')
      setSelectedLeadIds(getIdList(item.leads))
    }
    setForm(initial)
    setFilterLeads('')
  }, [modal, profiles])

  if (!modal) return null
  const fields = MODAL_FIELDS[modal.type] || []
  const setField = (key, value) => setForm(current => ({ ...current, [key]: value }))
  const toggleLead = id => setSelectedLeadIds(current => current.includes(id) ? current.filter(x => x !== id) : [...current, id])

  const submit = e => {
    e.preventDefault()
    const payload = { ...form }
    if (modal.type === 'lead') payload.score = payload.score === '' ? null : Number(payload.score)
    if (modal.type === 'profile') payload.success_score = Number(payload.success_score || 0)
    if (modal.type === 'note') {
      payload.profile_id = Number(payload.profile_id)
      payload.profile = Number(payload.profile_id)
      payload.leads = selectedLeadIds
    }
    onSave(payload)
  }

  const matchedLeads = leads.filter(lead => `${lead.title || ''} ${lead.text || ''} ${lead.source || ''}`.toLowerCase().includes(filterLeads.toLowerCase()))
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
    <form className="modal" onSubmit={submit}>
      <div className="modal-head"><div><span className="eyebrow">{modal.item ? 'РЕДАКТИРОВАНИЕ' : 'НОВАЯ ЗАПИСЬ'}</span><h2>{modal.type === 'lead' ? 'Лид' : modal.type === 'profile' ? 'Профиль специалиста' : 'Заметка / задача'}</h2></div><IconButton icon={X} title="Закрыть" onClick={onClose} /></div>
      <div className="modal-body">
        <div className="form-grid">
          {fields.map(field => <label key={field.key} className={`form-field ${field.wide ? 'wide' : ''}`}>
            <span>{field.label}{field.required && <i> *</i>}</span>
            {field.type === 'textarea' ? <textarea required={field.required} value={form[field.key] ?? ''} onChange={e => setField(field.key, e.target.value)} rows={3} placeholder={field.placeholder || ''} /> :
              <input type={field.type || 'text'} required={field.required} min={field.min} max={field.max} step={field.step} value={form[field.key] ?? ''} onChange={e => setField(field.key, e.target.value)} placeholder={field.placeholder || ''} />}
          </label>)}
          {modal.type === 'note' && <>
            <label className="form-field wide"><span>Профиль специалиста *</span><select required value={form.profile_id ?? ''} onChange={e => setField('profile_id', e.target.value)}><option value="">Выбери профиль</option>{profiles.map(p => <option key={p.id} value={p.id}>#{p.id} · {shortText(p.description || p.stack || 'Без описания', 75)}</option>)}</select></label>
            <div className="form-field wide lead-picker"><span>Привязанные лиды · {selectedLeadIds.length}</span><SearchBox value={filterLeads} onChange={setFilterLeads} placeholder="Найти лид для заметки…" />
              <div className="checkbox-list">{matchedLeads.slice(0, 60).map(lead => <label key={lead.id} className="check-row"><input type="checkbox" checked={selectedLeadIds.includes(lead.id)} onChange={() => toggleLead(lead.id)} /><span><b>#{lead.id} {shortText(lead.title || lead.text, 80)}</b><small>{lead.source || 'Источник не указан'} · {lead.url || ''}</small></span></label>)}{matchedLeads.length === 0 && <span className="muted small">Лиды не найдены</span>}</div>
            </div>
          </>}
        </div>
      </div>
      <div className="modal-foot"><span className="muted small">Поля со звёздочкой обязательны.</span><div><Button variant="ghost" onClick={onClose}>Отмена</Button><Button type="submit" disabled={saving} icon={saving ? LoaderCircle : Check}>{saving ? 'Сохраняем…' : 'Сохранить'}</Button></div></div>
    </form>
  </div>
}

function Dashboard({ data, onNavigate, onOpenLead, refreshing, refresh }) {
  const leadCount = data.leads.length || objectCount(data.stats, 'leads')
  const profileCount = data.profiles.length || objectCount(data.stats, 'profiles')
  const noteCount = data.notes.length || objectCount(data.stats, 'notes')
  const issueCount = data.repositories.reduce((sum, repo) => sum + Number(repo.issues_count || (repo.issues?.length ?? 0)), 0)
  const hotLeads = data.leads.filter(lead => Number(lead.score) >= 0.7).length
  return <>
    <PageHeading page="dashboard" right={<Button variant="secondary" icon={RefreshCw} onClick={refresh} disabled={refreshing}>{refreshing ? 'Обновляем…' : 'Обновить данные'}</Button>} />
    <div className="hero-strip"><div className="hero-glow" /><div className="hero-copy"><Badge tone="mint"><Sparkles size={12} /> WORKSPACE</Badge><h2>Поиск возможностей.<br /><span>Меньше шума — больше пользы.</span></h2><p>Лиды, GitHub issues и сопоставление со специалистами — в одном рабочем пространстве.</p><Button icon={ArrowUpRight} onClick={() => onNavigate('leads')}>Открыть лиды</Button></div><div className="hero-art"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit-center"><Activity size={28} /></div><div className="orbit-chip chip-one"><Zap size={15} /> Lead score</div><div className="orbit-chip chip-two"><Github size={15} /> Issue scan</div><div className="orbit-chip chip-three"><Users size={15} /> Match</div></div></div>
    <div className="metric-grid">
      <MetricCard label="Всего лидов" value={leadCount} helper={`${hotLeads} с оценкой ≥ 0.7`} icon={Zap} tone="mint" />
      <MetricCard label="Профили специалистов" value={profileCount} helper="Доступно для сопоставления" icon={Users} tone="blue" />
      <MetricCard label="Заметки и задачи" value={noteCount} helper="Сохранённый рабочий контекст" icon={ClipboardList} tone="violet" />
      <MetricCard label="Репозитории GitHub" value={data.repositories.length} helper={`${issueCount} issues в выдаче`} icon={Github} tone="orange" />
    </div>
    <div className="dashboard-grid">
      <Panel title="Последние лиды" subtitle="Недавно добавленные записи" action={<Button size="sm" variant="ghost" onClick={() => onNavigate('leads')}>Все лиды <ChevronRight size={14} /></Button>}>
        {data.leads.length ? <div className="compact-list">{[...data.leads].slice(-5).reverse().map(lead => <button className="compact-row" key={lead.id} onClick={() => onOpenLead(lead)}><span className="source-avatar">{(lead.source || 'L').slice(0, 1).toUpperCase()}</span><span className="compact-main"><b>{lead.title || shortText(lead.text, 65) || `Лид #${lead.id}`}</b><small>{lead.source || 'Источник'} · #{lead.id}</small></span><Score value={lead.score} /><ChevronRight size={15} className="row-arrow" /></button>)}</div> : <EmptyState icon={Zap} title="Лидов пока нет">Когда коллекторы сохранят данные, они появятся здесь.</EmptyState>}
      </Panel>
      <Panel title="Состояние системы" subtitle="Связь с backend и данные анализа">
        <div className="system-list"><div className="system-row"><span className="system-mark"><Activity size={16} /></span><span><b>Flask API</b><small>{getApiBaseUrl()}</small></span><span className="status-label"><StatusDot online={Boolean(data.health?.ok ?? data.health?.status === 'ok')} />{data.health ? 'Доступен' : 'Нет ответа'}</span></div>
          <div className="system-row"><span className="system-mark"><Github size={16} /></span><span><b>GitHub pipeline</b><small>Репозитории и анализ issues</small></span><Badge tone={data.repositories.length ? 'mint' : 'neutral'}>{data.repositories.length ? 'Есть данные' : 'Пока пусто'}</Badge></div>
          <div className="system-row"><span className="system-mark"><Sparkles size={16} /></span><span><b>LLM provider</b><small>Текущий провайдер анализа</small></span><Badge tone={data.provider?.provider ? 'blue' : 'neutral'}>{data.provider?.provider || 'Не определён'}</Badge></div>
        </div>
        <div className="panel-callout"><div className="callout-icon"><CheckCheck size={17} /></div><div><b>Панель подключена к API</b><p>Все записи загружаются из Flask. Действия в интерфейсе изменяют данные в backend.</p></div></div>
      </Panel>
    </div>
    <div className="quick-links"><button onClick={() => onNavigate('profiles')}><span className="quick-icon violet"><Users size={18} /></span><span><b>Управление командой</b><small>Добавить или обновить профиль</small></span><ChevronRight size={16} /></button><button onClick={() => onNavigate('repositories')}><span className="quick-icon blue"><Github size={18} /></span><span><b>Изучить GitHub issues</b><small>Посмотреть результаты анализа</small></span><ChevronRight size={16} /></button><button onClick={() => onNavigate('settings')}><span className="quick-icon mint"><Settings2 size={18} /></span><span><b>Настройки LLM</b><small>Выбрать провайдера модели</small></span><ChevronRight size={16} /></button></div>
  </>
}

function LeadsPage({ leads, onCreate, onEdit, onDelete, onShare, shareResult }) {
  const [query, setQuery] = useState('')
  const [source, setSource] = useState('all')
  const [minScore, setMinScore] = useState('')
  const [selected, setSelected] = useState([])
  const sources = [...new Set(leads.map(x => x.source).filter(Boolean))]
  const rows = leads.filter(lead => {
    const haystack = `${lead.title || ''} ${lead.text || ''} ${lead.source || ''} ${lead.author || ''} ${lead.url || ''} ${lead.source_id || ''}`.toLowerCase()
    return haystack.includes(query.toLowerCase()) && (source === 'all' || lead.source === source) && (minScore === '' || Number(lead.score ?? 0) >= Number(minScore))
  })
  const toggle = id => setSelected(cur => cur.includes(id) ? cur.filter(x => x !== id) : [...cur, id])
  const toggleAll = () => setSelected(selected.length === rows.length ? [] : rows.map(x => x.id))
  return <>
    <PageHeading page="leads" right={<Button icon={Plus} onClick={onCreate}>Добавить лид</Button>} />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Название, текст, источник, автор…" /><label className="filter-select"><Filter size={14} /><select value={source} onChange={e => setSource(e.target.value)}><option value="all">Все источники</option>{sources.map(x => <option key={x} value={x}>{x}</option>)}</select></label><label className="score-filter"><span>Score ≥</span><input type="number" min="0" max="1" step="0.05" value={minScore} onChange={e => setMinScore(e.target.value)} placeholder="0.0" /></label><span className="toolbar-count">{rows.length} из {leads.length}</span></div>
    <Panel title="База лидов" subtitle="Фильтрация происходит по загруженным данным" action={<div className="panel-actions">{selected.length > 0 && <Button variant="secondary" size="sm" onClick={() => onShare(selected)}>{`Поделиться (${selected.length})`}</Button>}<span className="table-total">{rows.length} записей</span></div>}>
      {rows.length ? <div className="table-wrap"><table><thead><tr><th className="check-cell"><input type="checkbox" checked={rows.length > 0 && selected.length === rows.length} onChange={toggleAll} /></th><th>Лид</th><th>Источник</th><th>Автор</th><th>Score</th><th>Группа</th><th className="action-cell">Действия</th></tr></thead><tbody>{rows.map(lead => <tr key={lead.id}><td className="check-cell"><input type="checkbox" checked={selected.includes(lead.id)} onChange={() => toggle(lead.id)} /></td><td><div className="cell-title"><button className="text-link" onClick={() => window.open(lead.url, '_blank', 'noopener,noreferrer')}>{lead.title || shortText(lead.text, 62) || `Лид #${lead.id}`} <ExternalLink size={12} /></button><small>#{lead.id} · {lead.source_id || 'без source_id'}</small><p>{shortText(lead.text, 90)}</p></div></td><td><Badge>{lead.source || 'unknown'}</Badge></td><td>{showValue(lead.author)}</td><td><Score value={lead.score} /></td><td>{showValue(lead.group)}</td><td><div className="row-actions"><IconButton icon={FileText} title="Открыть источник" onClick={() => lead.url && window.open(lead.url, '_blank', 'noopener,noreferrer')} /><IconButton icon={Settings2} title="Редактировать" onClick={() => onEdit(lead)} /><IconButton icon={Trash2} title="Удалить" danger onClick={() => onDelete(lead)} /></div></td></tr>)}</tbody></table></div> : <EmptyState icon={Search} title={leads.length ? 'Ничего не найдено' : 'База пока пустая'}>{leads.length ? 'Измени запрос или параметры фильтра.' : 'Создай лид вручную или дождись результатов коллекторов.'}</EmptyState>}
      {shareResult && <div className="share-result"><Check size={15} /><div><b>Результат /share</b><pre>{shareResult}</pre></div></div>}
    </Panel>
  </>
}

function ProfilesPage({ profiles, onCreate, onEdit, onDelete }) {
  const [query, setQuery] = useState('')
  const rows = profiles.filter(p => `${p.stack || ''} ${p.experience || ''} ${p.description || ''} ${p.can_solve || ''}`.toLowerCase().includes(query.toLowerCase()))
  return <>
    <PageHeading page="profiles" right={<Button icon={Plus} onClick={onCreate}>Новый профиль</Button>} />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Навыки, опыт, описание…" /><span className="toolbar-count">{rows.length} профилей</span></div>
    {rows.length ? <div className="profile-grid">{rows.map((profile, index) => <article className="profile-card" key={profile.id}><div className="profile-card-top"><div className={`profile-avatar avatar-${index % 5}`}>{String(profile.description || profile.stack || 'P').trim().slice(0, 1).toUpperCase()}</div><div className="profile-heading"><div className="profile-id">SPECIALIST #{profile.id}</div><h3>{shortText(profile.description || 'Профиль без описания', 66)}</h3><span>{profile.experience || 'Опыт не указан'}</span></div><div className="profile-menu"><IconButton icon={Settings2} title="Редактировать" onClick={() => onEdit(profile)} /><IconButton icon={Trash2} title="Удалить" danger onClick={() => onDelete(profile)} /></div></div><div className="profile-stat"><span>Коэффициент успеха</span><Score value={profile.success_score} /></div><div className="profile-detail"><span>STACK</span><p>{profile.stack || 'Не указан'}</p></div><div className="profile-detail"><span>МОЖЕТ РЕШИТЬ</span><p>{profile.can_solve || 'Не указано'}</p></div><div className="profile-links">{profile.url_resume && <a href={profile.url_resume} target="_blank" rel="noreferrer"><FileText size={13} /> Резюме</a>}{profile.portfolio && <a href={profile.portfolio} target="_blank" rel="noreferrer"><Globe size={13} /> Портфолио</a>}{!profile.url_resume && !profile.portfolio && <span className="muted small">Ссылки не добавлены</span>}</div></article>)}</div> : <Panel><EmptyState icon={Users} title="Профилей не найдено">Добавь специалиста и укажи описание; stack, опыт и can_solve необязательны.</EmptyState></Panel>}
  </>
}

function NotesPage({ notes, profiles, leads, onCreate, onEdit, onDelete }) {
  const [query, setQuery] = useState('')
  const rows = notes.filter(n => `${n.text || ''} ${n.purpose || ''}`.toLowerCase().includes(query.toLowerCase()))
  const profileName = id => { const p = profiles.find(x => Number(x.id) === Number(id)); return p ? shortText(p.description || p.stack || `Профиль ${id}`, 54) : `Профиль #${id ?? '—'}` }
  const leadLookup = new Map(leads.map(l => [Number(l.id), l]))
  return <>
    <PageHeading page="notes" right={<Button icon={Plus} onClick={onCreate}>Добавить заметку</Button>} />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Найти заметку или следующий шаг…" /><span className="toolbar-count">{rows.length} записей</span></div>
    {rows.length ? <div className="notes-grid">{rows.map(note => <article className="note-card" key={note.id}><div className="note-top"><span className="note-id">NOTE / {String(note.id).padStart(3, '0')}</span><div className="row-actions"><IconButton icon={Settings2} title="Редактировать" onClick={() => onEdit(note)} /><IconButton icon={Trash2} title="Удалить" danger onClick={() => onDelete(note)} /></div></div><h3>{note.text}</h3><p className="note-purpose">{note.purpose}</p><div className="note-meta"><span className="quick-icon violet"><Users size={14} /></span><span>{profileName(note.profile_id ?? note.profile)}</span></div><div className="note-leads"><span className="detail-label">СВЯЗАННЫЕ ЛИДЫ</span><div className="note-tags">{getIdList(note.leads).length ? getIdList(note.leads).map(id => <a href={leadLookup.get(id)?.url || '#'} target="_blank" rel="noreferrer" key={id} className="note-tag">#{id} {shortText(leadLookup.get(id)?.title || 'Лид', 35)}</a>) : <span className="muted small">Лиды не привязаны</span>}</div></div></article>)}</div> : <Panel><EmptyState icon={ClipboardList} title="Заметок нет">Свяжи задачу с профилем специалиста и нужными лидами.</EmptyState></Panel>}
  </>
}

function RepositoriesPage({ repositories, onOpenRepository, selectedRepo, selectedIssue, onOpenIssue, issueLoading, onBackToRepos }) {
  const [query, setQuery] = useState('')
  const [issueQuery, setIssueQuery] = useState('')
  const [tab, setTab] = useState('issues')
  const [extra, setExtra] = useState({ comments: [], analysis: null, loading: false, error: '' })
  const repoRows = repositories.filter(r => String(r.full_name || '').toLowerCase().includes(query.toLowerCase()))
  useEffect(() => {
    let alive = true
    if (!selectedIssue) { setExtra({ comments: [], analysis: null, loading: false, error: '' }); return () => { alive = false } }
    setExtra({ comments: [], analysis: null, loading: true, error: '' })
    Promise.allSettled([get(`/issues/${selectedIssue.id}/comments`), get(`/issues/${selectedIssue.id}/analysis`)]).then(results => {
      if (!alive) return
      setExtra({ comments: results[0].status === 'fulfilled' ? asArray(results[0].value, ['comments']) : [], analysis: results[1].status === 'fulfilled' ? results[1].value : selectedIssue.analysis || null, loading: false, error: results.every(r => r.status === 'rejected') ? 'Не удалось загрузить дополнительные данные.' : '' })
    })
    return () => { alive = false }
  }, [selectedIssue?.id])

  if (selectedIssue) {
    const comments = extra.comments.length ? extra.comments : asArray(selectedIssue.comments, ['comments'])
    const analysis = extra.analysis || selectedIssue.analysis || null
    return <>
      <PageHeading page="repositories" right={<Button variant="secondary" icon={ChevronLeft} onClick={() => onOpenIssue(null)}>К списку issues</Button>} />
      <div className="breadcrumb"><button onClick={onBackToRepos}>Репозитории</button><ChevronRight size={13} /><button onClick={onBackToRepos}>{selectedRepo?.full_name || 'Repository'}</button><ChevronRight size={13} /><span>Issue #{selectedIssue.number ?? selectedIssue.id}</span></div>
      <div className="issue-layout"><div className="issue-main"><Panel title={selectedIssue.title || `Issue #${selectedIssue.number ?? selectedIssue.id}`} subtitle={`${selectedRepo?.full_name || `Repository #${selectedIssue.repository_id}`} · Issue #${selectedIssue.number ?? selectedIssue.id}`} action={<Badge tone="blue">GitHub issue</Badge>}><div className="issue-body">{selectedIssue.body || 'У issue нет описания.'}</div>{selectedIssue.html_url && <a className="external-link" href={selectedIssue.html_url} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Открыть на GitHub</a>}</Panel>
        <Panel title={`Комментарии (${comments.length})`} subtitle="Комментарии к issue из базы данных">{extra.loading ? <LoadingState /> : comments.length ? <div className="comment-list">{comments.map(comment => <article className="comment" key={comment.id ?? comment.github_id}><div className="comment-avatar"><Code2 size={15} /></div><div><div className="comment-head"><b>Комментарий #{comment.id ?? comment.github_id}</b><span>{comment.score != null ? `Score ${percent(comment.score)}` : ''}</span></div><p>{comment.body || 'Пустой комментарий'}</p></div></article>)}</div> : <EmptyState icon={FileText} title="Комментарии не найдены">API пока не вернул комментарии для этой issue.</EmptyState>}</Panel></div>
        <aside className="issue-side"><Panel title="LLM-анализ" subtitle="Из сохранённой записи">{extra.loading ? <LoadingState /> : analysis ? <><div className="analysis-score"><span>Релевантность</span><strong>{percent(analysis.score)}</strong></div><div className="score-track large"><span style={{ width: `${Math.max(0, Math.min(100, Number(analysis.score || 0) * 100))}%` }} /></div><div className="analysis-label"><span>Label</span><Badge tone={analysis.label === 'helpful_lead' ? 'mint' : analysis.label === 'not_helpful' ? 'rose' : 'orange'}>{analysis.label || 'uncertain'}</Badge></div><div className="analysis-reason"><span>Причина</span><p>{analysis.reason || 'Объяснение не сохранено.'}</p></div><div className="analysis-reason"><span>Модель</span><p>{analysis.model_version || 'Не указана'}</p></div></> : <EmptyState icon={Sparkles} title="Нет анализа">Для этой issue пока нет сохранённого результата.</EmptyState>}</Panel>
          <Panel title="Сопоставление профиля">{selectedIssue.profile_matching ? <><b>{`Профиль #${selectedIssue.profile_matching.best_profile_id ?? '—'}`}</b><div className="analysis-score"><span>Match score</span><strong>{percent(selectedIssue.profile_matching.match_score)}</strong></div><p className="muted small">{selectedIssue.profile_matching.match_explanation}</p></> : <span className="muted small">Данные сопоставления не вложены в ответ issue.</span>}</Panel>
        </aside></div>
    </>
  }

  if (selectedRepo) {
    const issues = asArray(selectedRepo.issues, ['issues']).filter(issue => `${issue.title || ''} ${issue.body || ''} ${issue.number || ''}`.toLowerCase().includes(issueQuery.toLowerCase()))
    return <>
      <PageHeading page="repositories" right={<Button variant="secondary" icon={ChevronLeft} onClick={onBackToRepos}>Все репозитории</Button>} />
      <div className="repo-title-row"><div className="repo-big-icon"><Github size={24} /></div><div><h2>{selectedRepo.full_name || `Repository #${selectedRepo.id}`}</h2><p>GitHub repository · {issues.length} issues загружено</p></div><a className="external-link compact" href={`https://github.com/${selectedRepo.full_name}`} target="_blank" rel="noreferrer"><ExternalLink size={14} /> GitHub</a></div>
      <div className="toolbar panel"><SearchBox value={issueQuery} onChange={setIssueQuery} placeholder="Искать issue по заголовку или тексту…" /><span className="toolbar-count">{issues.length} issues</span></div>
      <Panel title="Issues репозитория" subtitle="Нажми на issue, чтобы открыть описание, комментарии и LLM-анализ">{issueLoading ? <LoadingState /> : issues.length ? <div className="issue-list">{issues.map(issue => <button className="issue-row" key={issue.id ?? issue.github_id} onClick={() => onOpenIssue(issue)}><span className="issue-number">#{issue.number ?? issue.id}</span><span className="issue-row-main"><b>{issue.title || 'Без заголовка'}</b><small>{shortText(issue.body, 120) || 'Описание отсутствует'}</small></span><span className="issue-row-tags">{issue.analysis?.label && <Badge tone={issue.analysis.label === 'helpful_lead' ? 'mint' : 'neutral'}>{issue.analysis.label}</Badge>}{issue.analysis?.score != null && <Score value={issue.analysis.score} />}</span><ChevronRight size={16} /></button>)}</div> : <EmptyState icon={Github} title="Issues не найдены">В ответе backend нет массива issues или он пуст.</EmptyState>}</Panel>
    </>
  }

  return <>
    <PageHeading page="repositories" />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Название репозитория…" /><span className="toolbar-count">{repoRows.length} репозиториев</span></div>
    <Panel title="Репозитории" subtitle="Список, сохранённый GitHub-коллектором">{repoRows.length ? <div className="repo-grid">{repoRows.map(repo => <button className="repo-card" key={repo.id} onClick={() => onOpenRepository(repo)}><div className="repo-card-top"><span className="repo-big-icon"><Github size={20} /></span><Badge>{repo.issues_count ?? repo.issues?.length ?? 0} issues</Badge></div><h3>{repo.full_name || `Repository #${repo.id}`}</h3><p>GitHub ID: {showValue(repo.github_id)}</p><div className="repo-card-bottom"><span>Сканирование: {repo.last_scanned_at ? new Date(repo.last_scanned_at).toLocaleString() : '—'}</span><ChevronRight size={15} /></div></button>)}</div> : <EmptyState icon={Github} title="Репозиториев пока нет">После запуска GitHub discovery найденные репозитории отобразятся здесь.</EmptyState>}</Panel>
  </>
}

function MatchingPage({ matches, profiles, repositories, onOpenIssue }) {
  const [query, setQuery] = useState('')
  const rows = matches.filter(x => `${x.issue_id ?? ''} ${x.best_profile_id ?? ''} ${x.match_explanation || ''}`.toLowerCase().includes(query.toLowerCase()))
  const profileLookup = new Map(profiles.map(p => [Number(p.id), p]))
  const repoLookup = new Map(repositories.map(r => [Number(r.id), r]))
  return <>
    <PageHeading page="matching" />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Issue ID, профиль, объяснение…" /><span className="toolbar-count">{rows.length} результатов</span></div>
    <Panel title="Результаты сопоставления" subtitle="Каждая запись показывает лучшего специалиста для issue">{rows.length ? <div className="table-wrap"><table><thead><tr><th>Issue</th><th>Профиль</th><th>Match score</th><th>Объяснение</th><th>Запись</th></tr></thead><tbody>{rows.map(row => { const profile = profileLookup.get(Number(row.best_profile_id)); return <tr key={row.id}><td><b>#{row.issue_id}</b><small className="table-sub">match #{row.id}</small></td><td>{profile ? <><b>{shortText(profile.description || profile.stack, 70)}</b><small className="table-sub">Профиль #{profile.id}</small></> : showValue(row.best_profile_id, 'Не назначен')}</td><td><Score value={row.match_score} /></td><td><div className="cell-title"><p>{shortText(row.match_explanation, 220)}</p></div></td><td><button className="text-link match-issue-link" onClick={() => onOpenIssue?.({ id: row.issue_id, number: row.issue_id })}>#{showValue(row.issue_id, '—')} <ChevronRight size={12} /></button></td></tr>})}</tbody></table></div> : <EmptyState icon={Layers3} title="Нет результатов сопоставления">Они появятся, когда pipeline сохранит строки в profile_matching.</EmptyState>}</Panel>
  </>
}

function TrainingPage({ samples }) {
  const [query, setQuery] = useState('')
  const [label, setLabel] = useState('all')
  const labels = [...new Set(samples.map(x => x.label).filter(Boolean))]
  const rows = samples.filter(x => `${x.text || ''} ${x.reason || ''} ${x.issue_id || ''}`.toLowerCase().includes(query.toLowerCase()) && (label === 'all' || x.label === label))
  return <>
    <PageHeading page="training" />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Поиск по тексту примера…" /><label className="filter-select"><SlidersHorizontal size={14} /><select value={label} onChange={e => setLabel(e.target.value)}><option value="all">Все метки</option>{labels.map(x => <option key={x} value={x}>{x}</option>)}</select></label><span className="toolbar-count">{rows.length} примеров</span></div>
    <Panel title="Dataset" subtitle="Примеры с оценкой, label и объяснением">{rows.length ? <div className="training-list">{rows.map(sample => <article className="training-card" key={sample.id}><div className="training-card-head"><span className="training-id">SAMPLE #{sample.id}</span><Badge tone={sample.label === 'helpful_lead' ? 'mint' : sample.label === 'not_helpful' ? 'rose' : 'orange'}>{sample.label || 'без метки'}</Badge></div><p className="training-text">{sample.text}</p><div className="training-foot"><div><span className="detail-label">ОЦЕНКА</span><Score value={sample.score} /></div><div><span className="detail-label">ISSUE ID</span><b>#{sample.issue_id}</b></div></div>{sample.reason && <div className="training-reason"><span>Обоснование</span><p>{sample.reason}</p></div>}</article>)}</div> : <EmptyState icon={BookOpen} title="Обучающих примеров нет">Таблица training_sample пока пуста или не отвечает.</EmptyState>}</Panel>
  </>
}

function FindedPage({ records }) {
  const [query, setQuery] = useState('')
  const [group, setGroup] = useState('all')
  const groups = [...new Set(records.map(x => x.group).filter(Boolean))]
  const rows = records.filter(x => `${x.group || ''} ${x.priznak || ''}`.toLowerCase().includes(query.toLowerCase()) && (group === 'all' || x.group === group))
  return <>
    <PageHeading page="finded" />
    <div className="toolbar panel"><SearchBox value={query} onChange={setQuery} placeholder="Признак или группа…" /><label className="filter-select"><Filter size={14} /><select value={group} onChange={e => setGroup(e.target.value)}><option value="all">Все группы</option>{groups.map(x => <option key={x} value={x}>{x}</option>)}</select></label><span className="toolbar-count">{rows.length} признаков</span></div>
    <Panel title="Сохранённые признаки" subtitle="Данные из таблицы finded">{rows.length ? <div className="table-wrap"><table><thead><tr><th>ID</th><th>Группа</th><th>Признак</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td className="muted">#{row.id}</td><td><Badge tone="blue">{row.group}</Badge></td><td><b>{row.priznak}</b></td></tr>)}</tbody></table></div> : <EmptyState icon={Search} title="Признаки не найдены">Добавь данные или запусти соответствующий сборщик.</EmptyState>}</Panel>
  </>
}

function SettingsPage({ provider, settings, onProviderChange, providerSaving }) {
  const [selected, setSelected] = useState(provider?.provider || '')
  useEffect(() => setSelected(provider?.provider || ''), [provider?.provider])
  const available = asArray(provider?.available)
  return <>
    <PageHeading page="settings" />
    <div className="settings-grid"><Panel title="Провайдер LLM" subtitle="Выбранный провайдер используется backend-сервисом для анализа и сопоставления."><div className="provider-current"><span className="provider-logo"><Sparkles size={20} /></span><div><span className="detail-label">ТЕКУЩИЙ ПРОВАЙДЕР</span><h3>{provider?.provider || 'Не удалось определить'}</h3><p>Значение хранится в app_settings под ключом llm_provider.</p></div><Badge tone={provider?.provider ? 'mint' : 'neutral'}>{provider?.provider ? 'Активен' : 'Неизвестен'}</Badge></div><label className="form-field provider-select"><span>Выбери провайдера</span><select value={selected} onChange={e => setSelected(e.target.value)}><option value="">Выбрать…</option>{available.map(item => <option key={String(item)} value={typeof item === 'string' ? item : item.value}>{typeof item === 'string' ? item : item.label || item.value}</option>)}</select></label><div className="form-actions"><Button icon={Check} disabled={!selected || selected === provider?.provider || providerSaving} onClick={() => onProviderChange(selected)}>{providerSaving ? 'Сохраняем…' : 'Сохранить провайдера'}</Button></div>{!available.length && <div className="inline-warning"><AlertCircle size={16} /><span>API не вернул список available. Проверь GET /context_provider.</span></div>}</Panel>
      <Panel title="Настройки приложения" subtitle="Ключи и значения, которые хранит backend.">{settings.length ? <div className="setting-list">{settings.map(item => <div className="setting-row" key={item.key}><span className="setting-key">{item.key}</span><code>{String(item.value)}</code></div>)}</div> : <EmptyState icon={Database} title="Настроек нет">Эндпоинт /app-settings вернул пустой список.</EmptyState>}</Panel>
    </div>
    <Panel title="Соединение с backend" subtitle="Адрес берётся из VITE_API_URL в frontend/.env"><div className="connection-box"><span className="connection-icon"><Globe size={18} /></span><div><b>{getApiBaseUrl()}</b><p>Frontend вызывает Flask API напрямую из браузера.</p></div><Badge tone="blue">REST API</Badge></div><div className="inline-warning"><AlertCircle size={16} /><span>Если запросы блокируются браузером, разреши CORS в Flask для адреса frontend (обычно http://localhost:5173).</span></div></Panel>
  </>
}

function App() {
  const [page, setPage] = useState('dashboard')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [data, setData] = useState(EMPTY_DATA)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [pageErrors, setPageErrors] = useState({})
  const [toast, setToast] = useState(null)
  const [modal, setModal] = useState(null)
  const [saving, setSaving] = useState(false)
  const [providerSaving, setProviderSaving] = useState(false)
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [issueLoading, setIssueLoading] = useState(false)
  const [shareResult, setShareResult] = useState('')

  const notify = useCallback((message, type = 'success') => {
    setToast({ message, type })
    window.clearTimeout(notify.timer)
    notify.timer = window.setTimeout(() => setToast(null), 4600)
  }, [])

  const loadData = useCallback(async (quiet = false) => {
    quiet ? setRefreshing(true) : setLoading(true)
    const requests = [
      ['leads', '/leads', v => asArray(v, ['leads'])],
      ['profiles', '/profiles', v => asArray(v, ['profiles'])],
      ['notes', '/notes', v => asArray(v, ['notes'])],
      ['repositories', '/repositories', v => asArray(v, ['repositories'])],
      ['matching', '/profile-matching', v => asArray(v, ['results', 'matches', 'profile_matching'])],
      ['training', '/training-samples', v => asArray(v, ['samples', 'training_samples'])],
      ['finded', '/finded', v => asArray(v, ['finded', 'items'])],
      ['settings', '/app-settings', v => asArray(v, ['settings', 'app_settings'])],
      ['provider', '/context_provider', v => v],
      ['stats', '/stats', v => v],
      ['health', '/health', v => v],
    ]
    const results = await Promise.allSettled(requests.map(([, path]) => get(path)))
    const next = { ...EMPTY_DATA }
    const errors = {}
    results.forEach((result, index) => {
      const [key, path, parser] = requests[index]
      if (result.status === 'fulfilled') next[key] = parser(result.value)
      else errors[key] = { path, message: result.reason?.message || 'Неизвестная ошибка' }
    })
    setData(next)
    setPageErrors(errors)
    setLoading(false)
    setRefreshing(false)
    if (Object.keys(errors).length) {
      const coreErrors = Object.keys(errors).filter(k => ['leads', 'profiles', 'repositories'].includes(k))
      if (coreErrors.length) console.warn('Some API sections could not be loaded', errors)
    }
    return { next, errors }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const refresh = async () => {
    const result = await loadData(true)
    notify(Object.keys(result.errors).length ? 'Данные обновлены, некоторые разделы недоступны.' : 'Данные обновлены.')
  }

  const navigate = id => { setPage(id); setMobileNavOpen(false); if (id !== 'repositories') { setSelectedRepo(null); setSelectedIssue(null) } }
  const openModal = (type, item = null) => setModal({ type, item })

  const saveRecord = async payload => {
    if (!modal) return
    setSaving(true)
    try {
      if (modal.type === 'lead') {
        if (modal.item?.id) await put(`/leads/${modal.item.id}`, payload)
        else await post('/leads', payload)
      } else if (modal.type === 'profile') {
        if (modal.item?.id) await put(`/profile/${modal.item.id}`, payload)
        else await post('/profile', payload)
      } else {
        if (modal.item?.id) await put(`/notes/${modal.item.id}`, payload)
        else await post('/notes', payload)
      }
      setModal(null)
      notify(`${modal.type === 'lead' ? 'Лид' : modal.type === 'profile' ? 'Профиль' : 'Заметка'} ${modal.item ? 'обновлён' : 'создана'}.`)
      await loadData(true)
    } catch (e) { notify(e.message, 'error') }
    finally { setSaving(false) }
  }

  const deleteRecord = async (type, item) => {
    const name = type === 'lead' ? 'лид' : type === 'profile' ? 'профиль' : 'заметку'
    if (!window.confirm(`Удалить ${name} #${item.id}? Это действие нельзя отменить.`)) return
    try {
      const path = type === 'lead' ? `/leads/${item.id}` : type === 'profile' ? `/profile/${item.id}` : `/notes/${item.id}`
      await del(path)
      notify(`${name[0].toUpperCase()}${name.slice(1)} удалён.`)
      await loadData(true)
    } catch (e) { notify(e.message, 'error') }
  }

  const shareLeads = async ids => {
    try {
      setShareResult('')
      for (const id of ids) await post('/choose', { id })
      const result = await post('/share', {})
      const text = typeof result === 'string' ? result : JSON.stringify(result, null, 2)
      setShareResult(text)
      notify('Запрошена выдача ссылок для выбранных лидов.')
    } catch (e) { notify(`Не удалось выполнить /share: ${e.message}`, 'error') }
  }

  const openRepository = async repo => {
    setIssueLoading(true)
    setSelectedIssue(null)
    try {
      const full = await get(`/repositories/${repo.id}`)
      setSelectedRepo(full)
    } catch (e) {
      setSelectedRepo(repo)
      notify(`Не удалось загрузить детали репозитория: ${e.message}`, 'error')
    } finally { setIssueLoading(false) }
  }

  const openIssue = async issue => {
    if (!issue) { setSelectedIssue(null); return }
    setIssueLoading(true)
    try {
      const detail = await get(`/issues/${issue.id}`)
      setSelectedIssue(detail)
    } catch (e) {
      setSelectedIssue(issue)
      notify(`Не удалось загрузить issue целиком: ${e.message}`, 'error')
    } finally { setIssueLoading(false) }
  }

  const changeProvider = async provider => {
    setProviderSaving(true)
    try {
      const result = await put('/context_provider', { provider })
      setData(current => ({ ...current, provider: result }))
      notify(`LLM provider изменён на ${provider}.`)
    } catch (e) { notify(e.message, 'error') }
    finally { setProviderSaving(false) }
  }

  const errorCount = Object.keys(pageErrors).length
  const pageError = pageErrors[page]
  const content = useMemo(() => {
    if (loading) return <div className="page-content"><LoadingState /></div>
    if (page === 'dashboard') return <Dashboard data={data} onNavigate={navigate} onOpenLead={lead => { setPage('leads'); }} refreshing={refreshing} refresh={refresh} />
    if (page === 'leads') return <LeadsPage leads={data.leads} onCreate={() => openModal('lead')} onEdit={x => openModal('lead', x)} onDelete={x => deleteRecord('lead', x)} onShare={shareLeads} shareResult={shareResult} />
    if (page === 'profiles') return <ProfilesPage profiles={data.profiles} onCreate={() => openModal('profile')} onEdit={x => openModal('profile', x)} onDelete={x => deleteRecord('profile', x)} />
    if (page === 'notes') return <NotesPage notes={data.notes} profiles={data.profiles} leads={data.leads} onCreate={() => openModal('note')} onEdit={x => openModal('note', x)} onDelete={x => deleteRecord('note', x)} />
    if (page === 'repositories') return <RepositoriesPage repositories={data.repositories} onOpenRepository={openRepository} selectedRepo={selectedRepo} selectedIssue={selectedIssue} onOpenIssue={openIssue} issueLoading={issueLoading} onBackToRepos={() => { setSelectedRepo(null); setSelectedIssue(null) }} />
    if (page === 'matching') return <MatchingPage matches={data.matching} profiles={data.profiles} repositories={data.repositories} onOpenIssue={issue => { setPage('repositories'); openIssue(issue) }} />
    if (page === 'training') return <TrainingPage samples={data.training} />
    if (page === 'finded') return <FindedPage records={data.finded} />
    if (page === 'settings') return <SettingsPage provider={data.provider} settings={data.settings} onProviderChange={changeProvider} providerSaving={providerSaving} />
    return null
  }, [page, loading, data, refreshing, selectedRepo, selectedIssue, issueLoading, shareResult, providerSaving, pageErrors])

  return <div className="app-shell">
    {mobileNavOpen && <button className="mobile-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Закрыть меню" />}
    <aside className={`sidebar ${mobileNavOpen ? 'mobile-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><Activity size={20} strokeWidth={2.5} /></div><div className="brand-text"><b>LEAD<span>HUNTER</span></b><small>INTELLIGENCE WORKSPACE</small></div><IconButton icon={X} title="Закрыть меню" onClick={() => setMobileNavOpen(false)} /></div>
      <div className="workspace-switch"><span className="workspace-avatar">LH</span><span><b>Lead Intelligence</b><small>Personal workspace</small></span><ChevronDown size={14} /></div>
      <nav className="nav-list">{NAV.map((item, idx) => item.section ? <div className="nav-section" key={item.section}>{item.section}</div> : <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => navigate(item.id)}><item.icon size={17} strokeWidth={1.8} /><span>{item.label}</span>{item.id === 'leads' && data.leads.length > 0 && <span className="nav-count">{data.leads.length > 99 ? '99+' : data.leads.length}</span>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-status"><div className="status-title"><span><StatusDot online={Boolean(data.health?.ok ?? data.health?.status === 'ok')} /> API connection</span><Badge tone={data.health ? 'mint' : 'rose'}>{data.health ? 'ONLINE' : 'CHECK'}</Badge></div><small>{getApiBaseUrl()}</small><Button variant="ghost" size="sm" icon={RefreshCw} onClick={refresh} disabled={refreshing}>Проверить соединение</Button></div><div className="sidebar-footer"><span className="footer-avatar">LH</span><span><b>Workspace admin</b><small>Local development</small></span><MoreHorizontal size={17} /></div></div>
    </aside>
    <main className="main-area"><header className="topbar"><div className="topbar-left"><button className="mobile-menu-btn" onClick={() => setMobileNavOpen(true)} aria-label="Открыть меню"><Menu size={19} /></button><div className="breadcrumb-top"><span>Workspace</span><ChevronRight size={13} /><b>{PAGE_META[page]?.[0] || 'Панель'}</b></div></div><div className="topbar-right"><span className="environment-pill"><span className="environment-dot" /> LOCAL ENVIRONMENT</span><button className="top-icon-btn" onClick={refresh} title="Обновить данные" disabled={refreshing}><RefreshCw size={16} className={refreshing ? 'spin' : ''} /></button><div className="top-avatar">LH</div></div></header>
      <div className="page-content">
        {errorCount > 0 && <div className="api-warning"><AlertCircle size={17} /><div><b>Некоторые разделы не загрузились</b><p>{Object.entries(pageErrors).slice(0, 4).map(([key, value]) => `${key}: ${value.message}`).join(' · ')}</p></div><button onClick={refresh} title="Повторить"><RefreshCw size={15} /></button></div>}
        {pageError && <div className="section-error"><AlertCircle size={16} /><div><b>Проблема с разделом {page}</b><p>{pageError.message}</p><small>Проверь, что этот endpoint есть в app/main.py и Flask запущен.</small></div></div>}
        {content}
        <footer className="app-footer"><span>LEAD INTELLIGENCE HUNTER <span className="footer-dot">●</span> PRIVATE WORKSPACE</span><span>Flask API · React UI</span></footer>
      </div>
    </main>
    <RecordModal modal={modal} onClose={() => !saving && setModal(null)} onSave={saveRecord} profiles={data.profiles} leads={data.leads} saving={saving} />
    {toast && <div className={`toast ${toast.type}`}><span className="toast-icon">{toast.type === 'error' ? <AlertCircle size={17} /> : <Check size={17} />}</span><span>{toast.message}</span><button onClick={() => setToast(null)} aria-label="Закрыть уведомление"><X size={15} /></button></div>}
  </div>
}

export default App
