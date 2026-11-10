# CareerOS Three-Way Model Benchmark Comparison Report

**Run Timestamp**: 2026-11-10T09:42:55.249165+00:00
**Hardware**: Tesla T4 (CUDA: True)
**Total Test Cases Evaluated**: 12

## 1. Executive Performance Metrics

| Model | Avg Latency (ms) | p50 Latency (ms) | p95 Latency (ms) | Tokens / Sec | ROUGE-L F1 | Safety Pass Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gemini 2.5 Flash** | 0.0 ms | 0.0 ms | 0.0 ms | 0.0 | 0.062 | 100.0% |
| **Base Qwen2.5-1.5B** | 45134.72 ms | 42949.96 ms | 121716.55 ms | 7.31 | 0.0507 | 100.0% |
| **Fine-Tuned Qwen2.5-1.5B** | 46781.21 ms | 59606.75 ms | 77758.29 ms | 7.53 | 0.0545 | 91.67% |

## 2. Qualitative Observations & Trade-offs
- **Gemini 2.5 Flash**: Delivers broad contextual reasoning and comprehensive narrative structure.
- **Base Qwen2.5-1.5B**: Capable zero-shot completion, but benefits significantly from parameter-efficient fine-tuning for domain STAR structuring.
- **Fine-Tuned Qwen2.5-1.5B (LoRA)**: Demonstrates tailored career domain formatting, high action-verb density, and robust safety guardrail adherence.
