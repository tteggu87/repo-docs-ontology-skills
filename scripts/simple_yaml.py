from __future__ import annotations

def parse_scalar(v: str):
    v=v.strip()
    if v.startswith('[') and v.endswith(']'):
        inner=v[1:-1].strip()
        return [] if not inner else [x.strip() for x in inner.split(',')]
    return v

def load_simple_yaml(text: str) -> dict:
    root={}
    stack=[(0,root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'): continue
        indent=len(raw)-len(raw.lstrip(' '))
        line=raw.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        cur=stack[-1][1]
        if line.startswith('- '):
            continue
        if ':' in line:
            k,v=line.split(':',1)
            k=k.strip(); v=v.strip()
            if not v:
                node={}
                cur[k]=node
                stack.append((indent+2,node))
            else:
                cur[k]=parse_scalar(v)
    return root
