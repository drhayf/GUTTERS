from typing import Any
from .schemas import UniversalProtocolMessage

class ProtocolTranslator:
    def translate_to_protocol(
        self,
        source_agent: str,
        raw_output: Any,
        insight_type: str = "Pattern",
        confidence: float = 0.5,
    ) -> UniversalProtocolMessage:
        if isinstance(raw_output, dict):
            payload = raw_output
        elif hasattr(raw_output, "model_dump"):
            payload = raw_output.model_dump()
        elif hasattr(raw_output, "__dict__"):
            payload = raw_output.__dict__
        else:
            payload = {"raw": str(raw_output)}
        
        return UniversalProtocolMessage(
            source_agent=source_agent,
            target_layer="Orchestrator",
            insight_type=insight_type,
            confidence_score=max(0.0, min(1.0, confidence)),
            payload=payload,
            hrm_validated=False,
        )
    
    def translate_external_framework(
        self,
        framework_name: str,
        external_data: dict,
        mapping: dict[str, str] | None = None,
    ) -> UniversalProtocolMessage:
        if mapping:
            translated_payload = {}
            for external_key, protocol_key in mapping.items():
                if external_key in external_data:
                    translated_payload[protocol_key] = external_data[external_key]
            payload = translated_payload
        else:
            payload = {
                "framework": framework_name,
                "data": external_data,
            }
        
        return UniversalProtocolMessage(
            source_agent=f"{framework_name}Translator",
            target_layer="Orchestrator",
            insight_type="Fact",
            confidence_score=0.7,
            payload=payload,
            hrm_validated=False,
        )
    
    def merge_protocol_messages(
        self,
        messages: list[UniversalProtocolMessage],
    ) -> UniversalProtocolMessage:
        if not messages:
            return UniversalProtocolMessage(
                source_agent="Translator",
                target_layer="Orchestrator",
                insight_type="Pattern",
                confidence_score=0.0,
                payload={},
                hrm_validated=False,
            )
        
        merged_payload: dict[str, Any] = {}
        sources: list[str] = []
        total_confidence = 0.0
        all_validated = True
        
        for msg in messages:
            sources.append(msg.source_agent)
            merged_payload[msg.source_agent] = msg.payload
            total_confidence += msg.confidence_score
            all_validated = all_validated and msg.hrm_validated
        
        return UniversalProtocolMessage(
            source_agent="MergedTranslator",
            target_layer="Orchestrator",
            insight_type="Pattern",
            confidence_score=total_confidence / len(messages),
            payload={
                "sources": sources,
                "merged_insights": merged_payload,
            },
            hrm_validated=all_validated,
        )

translator = ProtocolTranslator()
