import json

class NeoWatcher:
    """
    Neo-Watcher (Agent World Counterpart)
    Observer and Denial-Signal Producer. No execution authority.
    """
    
    def __init__(self, trace_id: str):
        """
        Initialize the Watcher.
        trace_id MUST be passed from OpenClaw runtime to prevent audit fragmentation.
        """
        if not trace_id:
            raise ValueError("trace_id is required to initialize NeoWatcher")
        self.trace_id = trace_id
        self.max_evidence_snippet_length = 160

    def evaluate_signal(
        self,
        confidence: float,
        signal_type: str,
        reason_code: str = "NO_ANOMALY",
        reason_detail: str = "No anomaly detected.",
        evidence: dict | None = None,
    ) -> dict:
        """
        Evaluates and emits a structured JSON signal scoring the risk.
        Enforces scope escalation strictly by confidence metric.
        """
        # Confidence semantic normalization
        confidence = max(0.0, min(1.0, float(confidence)))
        
        # 1. No-signal fast path (Report Only validation)
        if signal_type == "report_only" or confidence <= 0.2:
            return self._build_signal(
                signal_type="report_only",
                confidence=min(confidence, 0.2), # clamp to max 0.2 for fast-path
                scope="task",
                reason_code="NO_ANOMALY",
                reason_detail="No anomaly detected.",
                evidence=None,
            )
            
        # 2. Scope constraints (Default task. Escalate only if highly confident)
        scope = "task"
        if confidence > 0.7 and signal_type in ["deny_recommendation", "quarantine_recommendation"]:
            scope = "agent"  # Escalate scope safely because confidence is high
            
        return self._build_signal(signal_type, confidence, scope, reason_code, reason_detail, evidence)

    def _build_signal(
        self,
        signal_type: str,
        confidence: float,
        scope: str,
        reason_code: str,
        reason_detail: str,
        evidence: dict | None,
    ) -> dict:
        signal = {
            "neo_signal_v1": {
                "type": signal_type,
                "confidence": confidence,
                "scope": scope,
                "reason_code": reason_code,
                "reason_detail": reason_detail,
                "trace_id": self.trace_id
            }
        }
        
        if evidence:
            signal["neo_signal_v1"]["evidence"] = evidence

        return signal
        
    def hook_pre_tool_call(self, tool_name: str, tool_args: dict) -> dict:
        """
        Hook before a tool is executed.
        Scans for unexpected parameter expansion or hidden instruction injections.
        """
        # MVP: Static heuristic approach based on Lyra's guard suggestion.
        # Deep inspection using LLM (Neo-Analyzer mode) would be trigged by these weak signals later.
        
        raw_args = json.dumps(tool_args)
        
        if "ignore past" in raw_args.lower() or "system prompt" in raw_args.lower():
            snippet = raw_args[: self.max_evidence_snippet_length]
            return self.evaluate_signal(
                confidence=0.85, 
                signal_type="deny_recommendation", 
                reason_code="PROMPT_INJECTION",
                reason_detail="Hidden instruction injection in string.",
                evidence={
                    "field": f"tool_args.{tool_name}",
                    "snippet": snippet,
                },
            )
            
        if len(raw_args) > 5000: # Arbitrary anomaly expansion pattern
            snippet = raw_args[: self.max_evidence_snippet_length]
            return self.evaluate_signal(
                confidence=0.5,
                signal_type="warn",
                reason_code="PARAMETER_EXPANSION",
                reason_detail="Unexpected parameter expansion detected.",
                evidence={
                    "field": f"tool_args.{tool_name}",
                    "snippet": snippet,
                },
            )
            
        return self.evaluate_signal(0.1, "report_only", reason_code="NO_ANOMALY", reason_detail="No anomaly detected.")
