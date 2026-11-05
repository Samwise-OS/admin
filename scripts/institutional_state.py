#!/usr/bin/env python3
"""Minimal deterministic institutional-state ledger. Python standard library only."""
import argparse, hashlib, json, pathlib, sys, datetime

KINDS={"decision","correction","capability","handoff","receipt"}
STATUSES={"proposed","observed","verified","pending"}
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def load(path):
    p=pathlib.Path(path)
    if not p.exists(): return []
    return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
def validate(records):
    seen=set(); verified=set()
    for n,r in enumerate(records,1):
        required={"id","kind","status","source","claim","evidence","parent","hash"}
        if not required.issubset(r): raise ValueError(f"record {n}: missing fields")
        if r["kind"] not in KINDS or r["status"] not in STATUSES: raise ValueError(f"record {n}: invalid kind/status")
        if r["id"] in seen: raise ValueError(f"record {n}: duplicate id")
        body={k:v for k,v in r.items() if k!="hash"}
        if digest(body)!=r["hash"]: raise ValueError(f"record {n}: hash mismatch")
        expected=records[n-2]["hash"] if n>1 else None
        if r["parent"]!=expected: raise ValueError(f"record {n}: broken hash chain")
        if r["status"]=="verified":
            ev=r["evidence"]
            if not isinstance(ev,dict) or not all(ev.get(k) for k in ("uri","test","result")):
                raise ValueError(f"record {n}: verified claim lacks reproducible evidence")
            verified.add(r["id"])
        seen.add(r["id"])
    return verified
def append(path,data):
    records=load(path);validate(records)
    data["parent"]=records[-1]["hash"] if records else None
    data["hash"]=digest(data)
    if any(r["id"]==data["id"] for r in records): raise ValueError("duplicate id")
    validate(records+[data])
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f: f.write(canonical(data)+"\n")
    return data["hash"]
def bootstrap(path):
    records=load(path);verified=validate(records)
    return {"ledger_sha256":hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() if pathlib.Path(path).exists() else None,
            "record_count":len(records),
            "verified":[r for r in records if r["id"] in verified],
            "pending":[r for r in records if r["status"]=="pending"]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--ledger",default="state/institutional.jsonl")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("append");a.add_argument("--record",required=True,help="JSON file with id/kind/status/source/claim/evidence")
    sub.add_parser("verify");sub.add_parser("bootstrap")
    x=p.parse_args()
    if x.cmd=="append":
        d=json.loads(pathlib.Path(x.record).read_text(encoding="utf-8"))
        print(append(x.ledger,d))
    elif x.cmd=="verify":
        r=load(x.ledger);validate(r);print(canonical({"ok":True,"records":len(r)}))
    else: print(json.dumps(bootstrap(x.ledger),indent=2,ensure_ascii=False))
if __name__=="__main__":
    try:main()
    except (ValueError,OSError,json.JSONDecodeError) as e:print(str(e),file=sys.stderr);sys.exit(1)
