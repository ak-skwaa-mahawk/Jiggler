"""
api.py — Platform Governance API
Wraps Strawman + HITL for Railway deployment.
CORS-enabled for Google Sites embed.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import json
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# ── inline Strawman (no external import needed for deploy) ────────────────────

ASSUMED_CONSENT = ["default","implied","opt-out","terms of service","tos",
                   "by using this service","continued use","automatic",
                   "system default","inherited"]
HIGH_STANDING   = ["data_share","delegation","account_action","financial",
                   "identity","irreversible","bulk_action","policy_change"]
OVERREACH       = ["all users","all data","unlimited","permanent","no appeal",
                   "no override","silent","background","without notification"]

def strawman_evaluate(proposal: dict) -> dict:
    flags = []
    deductions = 0.0

    basis = proposal.get("consent_basis","").lower()
    for p in ASSUMED_CONSENT:
        if p in basis:
            flags.append(f"ASSUMED_CONSENT: '{p}' is not active consent")
            deductions += 0.30
            break

    if not proposal.get("reversible", True):
        flags.append("IRREVERSIBLE: requires explicit named consent")
        deductions += 0.25
        if proposal.get("action_type","") in HIGH_STANDING:
            flags.append("HIGH_STANDING_IRREVERSIBLE: double penalty")
            deductions += 0.20

    scope = proposal.get("scope", [])
    if len(scope) > 5:
        flags.append(f"SCOPE_EXCESS: {len(scope)} scope items")
        deductions += 0.15

    full_text = (proposal.get("description","") + " " +
                 proposal.get("consent_basis","") + " " +
                 " ".join(scope)).lower()
    for p in OVERREACH:
        if p in full_text:
            flags.append(f"OVERREACH: '{p}' detected")
            deductions += 0.25

    affects = proposal.get("affects", [])
    if not affects or affects == ["*"] or "all" in [a.lower() for a in affects]:
        flags.append("UNNAMED_AFFECTED: affected parties not specifically named")
        deductions += 0.20

    action_type = proposal.get("action_type","")
    if action_type in HIGH_STANDING:
        if "explicit" not in basis and "named" not in basis:
            flags.append(f"HIGH_STANDING_ACTION: '{action_type}' requires explicit named consent")
            deductions += 0.20

    score = max(0.0, 1.0 - deductions)

    if score >= 0.75 and not flags:
        verdict = "PASS"
        reasoning = "Action passes Freeman standing test."
    elif score >= 0.50:
        verdict = "CHALLENGE"
        reasoning = f"Requires additional justification. {len(flags)} concern(s)."
    else:
        verdict = "BLOCK"
        reasoning = f"Blocked. {len(flags)} overreach flag(s)."

    return {
        "verdict": verdict,
        "score": round(score, 4),
        "flags": flags,
        "reasoning": reasoning,
        "action_id": proposal.get("action_id", "unknown"),
        "timestamp": time.time()
    }


# ── inline HITL store (file-backed) ──────────────────────────────────────────

LOG_PATH     = Path(os.getenv("HITL_LOG_PATH", "data/observation_log.json"))
WEIGHTS_PATH = Path(os.getenv("HITL_WEIGHTS_PATH", "data/weights_matrix.json"))

def _load_json(path, default):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default

def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))

def _wkey(actor, action_type):
    return f"{actor}::{action_type}"

def hitl_record(action_id, action_type, actor, observer_id,
                decision, weight=1.0, note=""):
    log     = _load_json(LOG_PATH, [])
    weights = _load_json(WEIGHTS_PATH, {})
    key     = _wkey(actor, action_type)

    record = {
        "record_id":   hashlib.sha256(f"{action_id}{observer_id}{time.time()}".encode()).hexdigest()[:16],
        "action_id":   action_id,
        "action_type": action_type,
        "actor":       actor,
        "observer_id": observer_id,
        "decision":    decision,
        "weight":      max(0.0, min(1.0, weight)),
        "note":        note,
        "timestamp":   time.time()
    }
    log.append(record)

    if key not in weights:
        weights[key] = {"actor": actor, "action_type": action_type,
                        "sanction": 0.0, "object": 0.0,
                        "abstain": 0.0, "count": 0}
    w = weights[key]
    w["count"] += 1
    if decision == "SANCTION":   w["sanction"] += record["weight"]
    elif decision == "OBJECT":   w["object"]   += record["weight"]
    else:                        w["abstain"]  += record["weight"]

    _save_json(LOG_PATH, log)
    _save_json(WEIGHTS_PATH, weights)
    return record

def hitl_stance(actor, action_type):
    weights = _load_json(WEIGHTS_PATH, {})
    key = _wkey(actor, action_type)
    if key not in weights:
        return {"actor": actor, "action_type": action_type,
                "net_score": 0.0, "confidence": 0.0,
                "stance": "UNOBSERVED", "count": 0}
    w = weights[key]
    total  = w["sanction"] + w["object"] + w["abstain"]
    active = w["sanction"] + w["object"]
    net    = (w["sanction"] - w["object"]) / total if total else 0.0
    conf   = active / total if total else 0.0

    if conf < 0.2:          stance = "UNOBSERVED"
    elif net >= 0.6:        stance = "SANCTIONED"
    elif net >= 0.2:        stance = "CAUTIOUSLY_APPROVED"
    elif net >= -0.2:       stance = "CONTESTED"
    elif net >= -0.6:       stance = "CAUTIOUSLY_OBJECTED"
    else:                   stance = "OBJECTED"

    return {"actor": actor, "action_type": action_type,
            "net_score": round(net, 4), "confidence": round(conf, 4),
            "stance": stance, "count": w["count"]}

def bias_scan():
    weights  = _load_json(WEIGHTS_PATH, {})
    findings = []
    for key, w in weights.items():
        total  = w["sanction"] + w["object"] + w["abstain"]
        active = w["sanction"] + w["object"]
        net    = (w["sanction"] - w["object"]) / total if total else 0.0
        conf   = active / total if total else 0.0

        if net < -0.2 and conf < 0.4:
            findings.append({"type": "LOW_CONFIDENCE_OBJECTION",
                             "actor": w["actor"], "action_type": w["action_type"],
                             "net_score": round(net,4), "confidence": round(conf,4)})
        if w["count"] < 3:
            findings.append({"type": "UNOBSERVED_ACTION",
                             "actor": w["actor"], "action_type": w["action_type"],
                             "count": w["count"]})
        if net >= 0.2 and w["object"] > 0:
            obj_ratio = w["object"] / (w["sanction"] + w["object"])
            if obj_ratio > 0.25:
                findings.append({"type": "TOLERANCE_STACK_WARNING",
                                 "actor": w["actor"], "action_type": w["action_type"],
                                 "objection_ratio": round(obj_ratio,4)})
    return findings


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "live", "platform": "ak-skwaa-mahawk/Platform",
                    "timestamp": time.time()})

@app.route("/strawman/evaluate", methods=["POST"])
def strawman_route():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    required = ["action_id","actor","action_type","description",
                "affects","reversible","consent_basis","scope"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400
    return jsonify(strawman_evaluate(data))

@app.route("/hitl/observe", methods=["POST"])
def hitl_observe():
    data = request.get_json(force=True)
    required = ["action_id","action_type","actor","observer_id","decision"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400
    if data["decision"] not in ("SANCTION","OBJECT","ABSTAIN"):
        return jsonify({"error": "decision must be SANCTION, OBJECT, or ABSTAIN"}), 400
    record = hitl_record(
        data["action_id"], data["action_type"], data["actor"],
        data["observer_id"], data["decision"],
        data.get("weight", 1.0), data.get("note", "")
    )
    return jsonify({"status": "recorded", "record": record})

@app.route("/hitl/stance", methods=["GET"])
def hitl_stance_route():
    actor       = request.args.get("actor","")
    action_type = request.args.get("action_type","")
    if not actor or not action_type:
        return jsonify({"error": "actor and action_type params required"}), 400
    return jsonify(hitl_stance(actor, action_type))

@app.route("/hitl/log", methods=["GET"])
def hitl_log():
    log = _load_json(LOG_PATH, [])
    action_id = request.args.get("action_id")
    if action_id:
        log = [r for r in log if r["action_id"] == action_id]
    return jsonify({"count": len(log), "log": log[-50:]})

@app.route("/hitl/bias", methods=["GET"])
def hitl_bias():
    return jsonify({"findings": bias_scan()})

@app.route("/platform/check", methods=["POST"])
def platform_check():
    """Full pipeline: Strawman → HITL stance → combined verdict."""
    data = request.get_json(force=True)
    strawman_result = strawman_evaluate(data)
    stance          = hitl_stance(data.get("actor",""), data.get("action_type",""))

    # Combined verdict
    if strawman_result["verdict"] == "BLOCK":
        final = "BLOCK"
    elif strawman_result["verdict"] == "CHALLENGE" or stance["stance"] in ("OBJECTED","CAUTIOUSLY_OBJECTED"):
        final = "CHALLENGE"
    elif stance["stance"] == "UNOBSERVED":
        final = "CHALLENGE"  # not enough human data yet
    else:
        final = strawman_result["verdict"]

    return jsonify({
        "final_verdict":  final,
        "strawman":       strawman_result,
        "hitl_stance":    stance,
        "timestamp":      time.time()
    })


@app.route("/chat", methods=["POST"])
def chat_proxy():
    """
    Proxy route for Claude API.
    Keeps the Anthropic API key server-side (set ANTHROPIC_API_KEY env var in Railway).
    Browser sends messages here, Railway calls Anthropic, returns response.
    Set CHAT_TOKEN env var in Railway to require a token from callers.
    """
    # ── optional access token check ──────────────────────────────────────────
    chat_token = os.getenv("CHAT_TOKEN", "")
    if chat_token:
        auth_header = request.headers.get("X-Chat-Token", "")
        body_token  = (request.get_json(force=True, silent=True) or {}).get("token", "")
        if auth_header != chat_token and body_token != chat_token:
            return jsonify({"error": "Unauthorized"}), 401

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY not set on server"}), 500

    data = request.get_json(force=True)
    messages = data.get("messages", [])
    system = data.get("system", "You are a helpful assistant.")

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    import urllib.request
    import urllib.error

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": system,
        "messages": messages
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            reply = result.get("content", [{}])[0].get("text", "No response.")
            return jsonify({"reply": reply})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return jsonify({"error": f"Anthropic API error: {e.code}", "detail": body}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
