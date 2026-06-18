# Lab 16 Benchmark Report - Reflexion Agent

## Executive Summary
This report compares **ReAct** (single-attempt reasoning) versus **Reflexion** (multi-attempt with self-reflection) on HotpotQA multi-hop questions.

**Key Finding**: Reflexion achieves **95.0%** accuracy compared to ReAct's **86.7%** accuracy, representing a **+8.3%** improvement at the cost of **+57.0%** tokens and **+89.8%** latency.

---

## Metadata
| Property | Value |
|----------|-------|
| Dataset | hotpot_processed.json |
| Mode | looping |
| Total Records | 240 |
| Agents Evaluated | react, reflexion |
| Total Tokens Used | 4,347,769 |
| Total Latency | 1,208,962ms (1209.0s) |

---

## Performance Comparison

### Accuracy (Exact Match)
| Metric | ReAct | Reflexion | Delta |
|--------|------:|----------:|------:|
| EM Score | 86.7% | 95.0% | +8.3% |
| Correct Answers | 104 | 114 | +10 |
| Wrong Answers | 16 | 6 | -10 |

### Efficiency Metrics
| Metric | ReAct | Reflexion | Delta | Change % |
|--------|------:|----------:|------:|---------:|
| Avg Attempts | 1.00 | 1.38 | +0.38 | +37.5% |
| Avg Tokens/Question | 14,099 | 22,132 | +8,033 | +57.0% |
| Avg Latency/Question | 3,476ms | 6,599ms | +3,123ms | +89.8% |
| Total Tokens | 1,691,887 | 2,655,882 | +963,995 | - |
| Cost Efficiency | - | - | 0.1462 | acc/token% |

---

## Failure Mode Analysis

| Failure Mode | ReAct | Reflexion | Total | Description |
|--------------|------:|----------:|------:|-------------|
| none | 104 | 114 | 218 | Question answered correctly |
| wrong_final_answer | 13 | 0 | 13 | Model selected incorrect entity as final answer despite processing relevant context |
| entity_drift | 4 | 1 | 5 | Model focused on wrong entity during multi-hop reasoning |
| incomplete_multi_hop | 0 | 4 | 4 | Model answered only the first hop of reasoning, failing to complete the full chain |
| looping | 0 | 1 | 1 | Model repeated the same wrong answer across multiple reflection attempts |


### Failure Mode Distribution
```
ReAct Failure Distribution:
  wrong_final_answer        ████ 13 (10.8%)
  entity_drift              █ 4 (3.3%)
  incomplete_multi_hop       0 (0.0%)
  looping                    0 (0.0%)

Reflexion Failure Distribution:
  wrong_final_answer         0 (0.0%)
  entity_drift               1 (0.8%)
  incomplete_multi_hop      █ 4 (3.3%)
  looping                    1 (0.8%)

---

## Extensions Implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding
- adaptive_max_attempts
- memory_compression

---

## Detailed Discussion

## Detailed Analysis

### Overall Performance
ReAct achieved 86.7% accuracy (EM) with an average of 1.0 attempt per question.
Reflexion achieved 95.0% accuracy with an average of 1.38 attempts per question.
This represents a +8.3% absolute improvement in accuracy.

### Cost-Benefit Analysis
The accuracy improvement of 8.3% came at the cost of:
- +57.0% more tokens (8033 additional tokens per question on average)
- +89.8% more latency (3123ms additional per question)
- Cost efficiency score: 0.1462 accuracy gain per 1% token increase

### Reflection Effectiveness
- Questions where Reflexion improved over ReAct: 11 (9.2%)
- Questions where Reflexion performed worse: 0
- Questions with unchanged performance: 6
- Average reflections used per question: 0.4

### Failure Mode Analysis
The most common failure modes were:
- **wrong_final_answer**: 13 cases (ReAct: 13, Reflexion: 0) - Model selected incorrect entity as final answer despite processing relevant context
- **entity_drift**: 4 cases (ReAct: 3, Reflexion: 1) - Model focused on wrong entity during multi-hop reasoning, drifting from the correct path
- **incomplete_multi_hop**: 4 cases (ReAct: 0, Reflexion: 4) - Model answered only the first hop of reasoning, failing to complete the full chain
- **looping**: 1 cases (ReAct: 0, Reflexion: 1) - Model repeated the same wrong answer across multiple reflection attempts

### Key Insights
1. **Reflection Memory Value**: The reflection memory allows the agent to learn from previous mistakes. When the first attempt fails, the reflector analyzes why and suggests a concrete strategy for the next attempt.

2. **Evaluator Quality Matters**: The evaluator's ability to correctly judge answers is critical. False positives (marking wrong answers as correct) terminate the reflection loop prematurely.

3. **Trade-off Consideration**: Reflexion is beneficial when accuracy is paramount and latency/token budget allows. For high-throughput applications, ReAct may be more practical.

### Recommendations
1. **Adaptive Max Attempts**: Use 2 attempts for easy questions, 3-4 for medium, and 5+ for hard questions based on initial confidence scores.
2. **Structured Evaluator**: Ground evaluations in specific evidence passages rather than just comparing final answers.
3. **Memory Compression**: Summarize reflection history to reduce token overhead while preserving key insights.
4. **Hybrid Approach**: Use ReAct as a fast path and only invoke Reflexion when the initial answer has low confidence.

### Limitations
- Token estimates are approximate based on API responses
- Latency includes only inference time, not network overhead
- Evaluation relies on exact match after normalization, which may not capture semantically correct answers


---

## Sample Predictions

### Correct Predictions (Sample)
| QID | Question | Gold Answer | Predicted | Attempts | Tokens |
|-----|----------|-------------|-----------|----------|--------|
| 5a7cd7f055429909bec7683e | What school was the actress who appeared with Michelle Willi... | Juilliard School | Juilliard School | 1 | 13,879 |
| 5a820f2f554299676cceb1ff | Although Michael Fincke's record was broken by Scott Kelly, ... | 381.6 days | 381.6 days | 1 | 14,509 |
| 5a8ffd705542995651fb5096 | Zamalek Sporting Club Centennial was a  friendly match again... | La Liga | La Liga | 1 | 13,512 |
| 5a88f9555542995153361214 | The Jeep Cherokee was originally sold as a variant of a Jeep... | 1963 to 1991 | 1963 to 1991 | 1 | 14,025 |
| 5a771d6155429966f1a36c6d | What lieutenant general stayed in the Elliott-Donaldson Hous... | Nathan Bedford Forrest | Nathan Bedford Forrest | 1 | 13,939 |

### Incorrect Predictions (Sample)
| QID | Question | Gold Answer | Predicted | Failure Mode | Attempts |
|-----|----------|-------------|-----------|--------------|----------|
| 5ab51ddf5542990594ba9d11 | Do both Lancaster Cathedral and Peel Cathedral belong to the... | yes | No.

Lancaster Cathedral is Roman Catholic, but Peel Cathedral is Anglican (it serves the Diocese of Sodor and Man, an Anglican diocese). | wrong_final_answer | 1 |
| 5abce2fc5542993a06baf994 | The board member of Goldman Sachs also founded a company wit... | McKinsey's offices | Looking at the context step by step:

1. **Board member of Goldman Sachs**: Rajat Gupta was a board member of Goldman Sachs.

2. **Company he founded**: Rajat Gupta co-founded the Indian School of Business.

3. **Co-founder**: Anil Kumar was the co-founder of the Indian School of Business with Rajat Gupta.

4. **What Anil Kumar co-founded**: Anil Kumar co-founded McKinsey's offices in Silicon Valley and India.

**McKinsey & Company** | wrong_final_answer | 1 |
| 5a78bd515542990784727749 | The show featuring a young boy named Gerald Bald Z premiered... | Cartoon Network | Adult Swim | wrong_final_answer | 1 |
| 5a85e5345542991dd0999ebb | Which mechanical device which engages and disengages power t... | hydraulic clutch | Hydraulic brake | wrong_final_answer | 1 |
| 5ac1a4ed5542994d76dcce90 | Are William James and Bret Easton Ellis both screenwriters? | no | No.

William James was a philosopher and psychologist, not a screenwriter. Bret Easton Ellis is described as an author, screenwriter, and short story writer. | entity_drift | 1 |

---

## Conclusion

The Reflexion architecture demonstrates measurable improvement over single-attempt ReAct on multi-hop QA tasks. The self-reflection mechanism enables the agent to:
1. Identify when its initial reasoning was flawed
2. Extract specific lessons from failures
3. Apply targeted strategies in subsequent attempts

However, this comes with increased computational cost. The optimal approach depends on the use case:
- **High-stakes applications**: Use Reflexion for maximum accuracy
- **Latency-sensitive applications**: Use ReAct for faster responses
- **Balanced approach**: Use adaptive max attempts based on question difficulty

**Overall Score: 95.0% accuracy with 1.38 average attempts**

---
*Report generated by Lab 16 Reflexion Agent Benchmark*
