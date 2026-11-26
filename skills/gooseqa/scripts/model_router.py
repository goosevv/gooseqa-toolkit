"""GooseQA capability-based advisory model routing; no model API calls."""
import json, os, pathlib, tempfile

ROLES = {"orchestrator":"BALANCED","explorer":"FAST","test_designer":"BALANCED","test_engineer":"BALANCED","visual_analyst":"VISION","reviewer":"REASONING","documentation":"FAST","test_runner":"CLI"}
ORIGINAL = {"explorer":["gpt-6-luna","medium"],"test_designer":["gpt-6.2-sol","medium"],"test_engineer":["gpt-6.2-sol","medium"],"visual_analyst":["gpt-6.1-terra","low"],"reviewer":["gpt-6.2-sol","medium"],"documentation":["gpt-6-luna","low"],"orchestrator":["gpt-6.2-sol","medium"]}
EFFORTS = ['low','medium','high']
PROFILES = {'ECO':0,'BALANCED':2,'QUALITY':4}
PROVIDERS = ['auto','codex','claude','gemini','generic']
DEFAULT = dict(version=1,provider='auto',profile='BALANCED',routing='auto',
               max_effort='medium',allow_fallback=True,max_agents=2,models={})

def settings_path():
    return pathlib.Path(os.environ.get('GOOSEQA_CONFIG',pathlib.Path.home()/'.gooseqa'/'model-settings.json')).expanduser()

def validate(value):
    if not isinstance(value,dict) or set(value)-set(DEFAULT):
        raise ValueError('Invalid model settings')
    c={**DEFAULT,**value}
    for k,choices in [('version',[1]),('provider',PROVIDERS),('profile',[*PROFILES,'CUSTOM']),
                      ('routing',['auto','manual','original']),('max_effort',EFFORTS)]:
        if c[k] not in choices: raise ValueError('Invalid '+k)
    if type(c['allow_fallback']) is not bool or type(c['max_agents']) is not int or not 0<=c['max_agents']<=8:
        raise ValueError('Invalid fallback or concurrency limit')
    if not isinstance(c['models'],dict) or set(c['models'])-set(ORIGINAL):
        raise ValueError('Invalid role mapping')
    if any(not isinstance(v,str) or not v.strip() or len(v)>160 for v in c['models'].values()):
        raise ValueError('Invalid model ID')
    return c

def load():
    path=settings_path()
    return validate(json.loads(path.read_text(encoding='utf-8'))) if path.exists() else validate({})

def save(value):
    c=validate(value); path=settings_path(); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='models-',suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(c,f,ensure_ascii=False,indent=2)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return c

def plan(settings,host):
    """Host capability inventory must be observed or explicitly supplied by user."""
    c=validate(settings)
    if not isinstance(host,dict): raise ValueError('Host must be an object')
    provider=host.get('provider','generic')
    if provider not in PROVIDERS[1:]: raise ValueError('Invalid host provider')
    mismatch=c['provider'] not in ('auto',provider)
    native=host.get('delegation') is True and not mismatch
    selectable=native and host.get('model_selection') is True
    limit=PROFILES.get(c['profile'],c['max_agents'])
    host_limit=host.get('max_agents',limit)
    if type(host_limit) is not int or host_limit<0: raise ValueError('Invalid host limit')
    limit=min(limit,host_limit) if native else 0
    inventory={}
    models=host.get('models',[])
    if not isinstance(models,list): raise ValueError('Invalid model inventory')
    for m in models:
        if not isinstance(m,dict) or not isinstance(m.get('id'),str) or not m['id'] or m['id'] in inventory:
            raise ValueError('Invalid or duplicate model ID')
        for field,allowed in [('classes',list(ROLES.values())[:-1]),('efforts',EFFORTS)]:
            if not isinstance(m.get(field,[]),list) or any(v not in allowed for v in m.get(field,[])):
                raise ValueError('Invalid '+field)
        inventory[m['id']]=m
    current=host.get('current_model')
    if current is not None and not isinstance(current,str): raise ValueError('Invalid current model')
    current_classes=host.get('current_classes',inventory.get(current,{}).get('classes',[]))
    if not isinstance(current_classes,list) or any(x not in list(ROLES.values())[:-1] for x in current_classes):
        raise ValueError('Invalid current classes')
    current_effort=host.get('current_effort')
    if current_effort is not None and current_effort not in EFFORTS: raise ValueError('Invalid current effort')
    strict=c['routing']=='original'
    fallback=c['allow_fallback'] and not strict
    cap=min(EFFORTS.index(c['max_effort']),1 if strict else 2)
    notices=[]
    if mismatch: notices.append('Configured provider differs from host; delegation disabled.')
    if not native: notices.append('Native delegation unavailable or unverified.')
    if native and not selectable: notices.append('Per-agent model selection unavailable or unverified.')
    if not current_effort: notices.append('Current effort is unverified; host must enforce any cap.')
    out={}
    for role,kind in ROLES.items():
        def blocked(reason): return dict(class_=kind,execution='blocked',reason=reason)
        if kind=='CLI':
            out[role]=dict(class_=kind,execution='cli',model=None,effort=None); continue
        exact,wanted=(ORIGINAL[role] if strict else (c['models'].get(role) if c['routing']=='manual' else None,None))
        if strict and provider!='codex':
            out[role]=blocked('Original preset requires Codex');continue
        if c['routing']=='manual' and not exact:
            out[role]=blocked('Manual model ID missing');continue
        def current_plan():
            if exact and current!=exact and not fallback: return blocked('Requested model is not the observed current model')
            if wanted and current_effort!=wanted: return blocked('Requested effort is not confirmed')
            if kind=='VISION' and kind not in current_classes: return blocked('Vision capability is unverified')
            if current_effort and EFFORTS.index(current_effort)>cap: return blocked('Current effort exceeds cap')
            result=dict(class_=kind,execution='current',model=current,effort=current_effort,reason='Host controls the existing session')
            if exact and current!=exact: result['fallback_from']=exact
            return result
        if role=='orchestrator' or not limit or not selectable:
            out[role]=current_plan();continue
        candidates=[]
        for model,m in inventory.items():
            if exact and model!=exact and not fallback: continue
            if not strict and kind not in m.get('classes',[]): continue
            if strict and (model!=exact or 'astra' in model.lower()): continue
            if kind=='VISION' and kind not in m.get('classes',[]): continue
            options=[e for e in m.get('efforts',[]) if EFFORTS.index(e)<=cap]
            if wanted:
                if wanted not in options:continue
                effort=wanted
            elif options:
                target=min(cap,0 if role in ('visual_analyst','documentation') else 1)
                effort=min(options,key=lambda e:abs(EFFORTS.index(e)-target))
            elif not m.get('efforts'): effort=None
            else:continue
            candidates.append((model,effort))
        candidates.sort(key=lambda x:x[0]!=exact if exact else False)
        if candidates:
            model,effort=candidates[0]
            out[role]=dict(class_=kind,execution='delegate',model=model,effort=effort,reason='Proposed, not executed')
            if exact and model!=exact:out[role]['fallback_from']=exact
        elif fallback:out[role]=current_plan()
        else:out[role]=blocked('No compatible selectable model')
    return dict(provider=provider,profile=c['profile'],max_concurrent_subagents=limit,
                roles=out,notices=notices,status='planned_not_executed')
