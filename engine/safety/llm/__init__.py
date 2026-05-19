"""engine.safety.llm — LLM 출력·페르소나·응답 일관성 (ADR-040)

이전 평면 (구→신):
  llm_output_sampler     → llm.output_sampler
  output_safety_gate     → llm.output_safety_gate
  output_token_guard     → llm.output_token_guard
  persona_self_eval      → llm.persona_self_eval
  response_*             → llm.response_*
  jailbreak_defense      → llm.jailbreak_defense
"""
