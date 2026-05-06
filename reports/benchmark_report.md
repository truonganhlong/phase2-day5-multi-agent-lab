# Báo cáo Benchmark — Single-Agent vs Multi-Agent

> Sinh bằng `python -m multi_agent_research_lab.cli benchmark` trên 3 query trong `configs/lab_default.yaml`.
> Output gốc của LLM giữ nguyên tiếng Anh để phản ánh đúng kết quả thật của benchmark; phần phân tích, tiêu đề và ghi chú đã dịch sang tiếng Việt.

## 1. Bảng tổng hợp

| Run | Latency (s) | Cost (USD) | Quality (0-10) | Ghi chú |
|---|---:|---:|---:|---|
| baseline-q1 | 18.80 | 0.0004 | 4.0 | errors=0 |
| multi-agent-q1 | 29.69 | 0.0015 | 9.0 | citation_coverage=1.0; errors=0; routes=researcher>analyst>writer>done |
| baseline-q2 | 7.86 | 0.0004 | 4.0 | errors=0 |
| multi-agent-q2 | 39.41 | 0.0014 | 9.0 | citation_coverage=1.0; errors=0; routes=researcher>analyst>writer>done |
| baseline-q3 | 8.12 | 0.0004 | 4.0 | errors=0 |
| multi-agent-q3 | 43.70 | 0.0015 | 9.0 | citation_coverage=1.0; errors=0; routes=researcher>analyst>writer>done |

## 2. Trung bình

- **Latency trung bình** — baseline: 11.59s, multi-agent: 37.60s (chậm hơn ~3.2x).
- **Cost trung bình** — baseline: 0.0004 USD, multi-agent: 0.0015 USD (đắt hơn ~3.7x).
- **Quality trung bình (rubric heuristic)** — baseline: 4.00, multi-agent: 9.00.
- **Citation coverage** — baseline: không có (single LLM call, không truy xuất nguồn), multi-agent: 1.0 ở cả 3 query.

## 3. Nhận xét chính

- Multi-agent **không nhanh hơn**, **không rẻ hơn**, nhưng output có nguồn rõ ràng và có cấu trúc theo từng giai đoạn (research → analysis → writing).
- Single-agent baseline phù hợp khi câu hỏi đơn giản hoặc cần trả lời nhanh.
- Multi-agent hợp lý khi yêu cầu trích dẫn nguồn, kiểm chứng được claim, hoặc câu hỏi phức tạp cần chia nhỏ.

## 4. Ví dụ output

### Q1: Research GraphRAG state-of-the-art and write a 500-word summary

**Output baseline (single-agent, 1 LLM call, không truy xuất nguồn):**

```
### Summary of GraphRAG: State-of-the-Art Research

**Introduction to GraphRAG**

GraphRAG (Graph Retrieval-Augmented Generation) is an innovative framework that combines the strengths of graph-based data representation with retrieval-augmented generation techniques. This approach is particularly relevant in the context of natural language processing (NLP) and knowledge representation, where the ability to effectively retrieve and generate information from structured data sources is crucial. The integration of graph structures allows for enhanced contextual understanding and reasoning capabilities, making it a significant advancement in the field.

**Key Findings**

1. **Graph Structure Utilization**: GraphRAG leverages graph structures to represent relationships and entities within a dataset. This representation allows for more nuanced information retrieval compared to traditional linear data structures. By modeling data as nodes and edges, GraphRAG can capture complex interdependencies and contextual relationships, which are often lost in simpler models.

2. **Retrieval-Augmented Generation**: The framework employs a retrieval mechanism that enhances the generative capabilities of language models. During the generation phase, GraphRAG retrieves relevant information from the graph, ensuring that the generated content is not only contextually appropriate but also factually accurate. This is particularly beneficial in applications requiring up-to-date information or specific domain knowledge.

3. **Performance Metrics**: Recent studies indicate that GraphRAG outperforms traditional generative models on various benchmarks, particularly in tasks involving question answering and summarization. The incorporation of graph-based retrieval mechanisms leads to improved precision and recall rates, as the model can access a broader range of relevant data points during the generation process.

4. **Scalability and Efficiency**: GraphRAG is designed to be scalable, accommodating large datasets without significant degradation in performance. The efficiency of the retrieval process is enhanced through optimized algorithms that prioritize relevant nodes and edges, reducing the computational overhead typically associated with graph traversal.

5. **Applications**: The versatility of GraphRAG allows it to be applied across multiple domains, including healthcare, finance, and education. For instance, in healthcare, it can assist in generating patient reports by retrieving relevant clinical data from a knowledge graph, thereby improving the accuracy and relevance of the generated text.

**Brief Analysis**

The integration of graph structures into the retrieval-augmented generation paradigm represents a significant leap forward in NLP capabilities. By utilizing the relational nature of graphs, GraphRAG can provide richer context and more accurate information, which is essential for applications requiring high levels of precision. This approach addresses some of the limitations of traditional generative models, which often struggle with maintaining context over longer texts or when faced with complex queries.

**Caveats**

Despite its advantages, there are several caveats to consider with GraphRAG:

- **Complexity of Graph Construction**: The effectiveness of GraphRAG is heavily dependent on the quality and structure of the underlying graph. Constructing comprehensive and accurate graphs can be resource-intensive and may require domain expertise.

- **Retrieval Limitations**: While the retrieval mechanism enhances generation, it may still struggle with ambiguous queries or when relevant data is sparse within the graph. This can lead to inaccuracies or irrelevant information being included in the generated output.

- **Computational Resources**: Although GraphRAG is designed to be efficient, the complexity of graph operations may still demand significant computational resources, particularly for very large datasets.

In conclusion, GraphRAG represents a promising advancement in the field of NLP by effectively combining graph-based data representation with retrieval-augmented generation techniques. Its ability to improve contextual understanding and information accuracy positions it as a valuable tool for technical learners and practitioners in the field.
```

**Output multi-agent (researcher → analyst → writer, có citations):**

```
### GraphRAG: A State-of-the-Art Approach to Retrieval-Augmented Generation

GraphRAG is an innovative framework that enhances the capabilities of Retrieval-Augmented Generation (RAG) by integrating knowledge graphs into the process. This structured, hierarchical approach seeks to improve the performance of language models, particularly in complex question-and-answer scenarios, by moving beyond traditional semantic search methods [1]. By creating a knowledge graph from an input corpus, GraphRAG allows for more nuanced reasoning and contextual understanding, thereby facilitating better information retrieval and generation [1][3].

#### Key Components of GraphRAG

The GraphRAG framework comprises several essential components: a query processor, retriever, organizer, generator, and data source. This holistic design enables the refinement of retrieved content before it is integrated with the original query [2]. Knowledge graphs play a pivotal role in this framework, providing structured relational information that enhances both retrieval and generation processes [3][4].

In contrast to baseline RAG systems that typically rely on vector databases to retrieve semantically similar text, GraphRAG’s incorporation of knowledge graphs significantly improves the contextual relevance of the information retrieved [3]. This is particularly beneficial when handling complex data, as the unique structure of graph-encoded data presents challenges that differ from traditional RAG systems, necessitating specialized designs for various domains [2].

#### Applications and Benefits

GraphRAG is designed for real-world applications across diverse fields, including scientific research and narrative analysis [4]. Its auto-tuning capabilities allow it to quickly adapt to new domains, enhancing its versatility and making it a valuable tool for complex data discovery [4]. The integration of GraphRAG with large language models (LLMs) further amplifies its potential by connecting these models to external data sources, leading to more accurate and contextually relevant outputs [3].

#### Performance Improvements

Research indicates that GraphRAG demonstrates substantial improvements in performance metrics for tasks requiring complex reasoning compared to traditional RAG methods [1][3]. While the framework shows promise, there are some gaps in empirical validation, as specific quantitative metrics or comparative studies against baseline RAG systems are not extensively documented [1][3]. Ongoing research aims to refine the GraphRAG framework and explore its applications across various domains, indicating a growing interest in the intersection of graph technology and language models [2][4].

#### Conclusion

In summary, GraphRAG represents a significant advancement in Retrieval-Augmented Generation by leveraging the power of knowledge graphs to enhance language models' capabilities in processing and reasoning about complex information. Its structured approach and adaptability position it as a promising tool for future applications across a range of disciplines, particularly in enhancing data discovery processes and improving the accuracy of outputs in applications requiring sophisticated reasoning.

### Sources
[1] Welcome - GraphRAG — https://microsoft.github.io/graphrag/
[2] Retrieval-Augmented Generation with Graphs (GraphRAG) - arXiv — https://arxiv.org/html/2501.00309v2
[3] GraphRAG Explained: Enhancing RAG with Knowledge Graphs — https://medium.com/@zilliz_learn/graphrag-explained-enhancing-rag-with-knowledge-graphs-3312065f99e1
[4] Project GraphRAG - Microsoft Research — https://www.microsoft.com/en-us/research/project/graphrag/
[5] A GraphRAG Approach to Query-Focused Summarization (Microsoft) — https://www.facebook.com/groups/470156308080157/posts/1202086618220452
```

### Q2: Compare single-agent and multi-agent workflows for customer support

**Output baseline:** (giữ nguyên tiếng Anh, xem file gốc trước khi dịch hoặc chạy lại lệnh `cli baseline -q "..."`).

**Output multi-agent:** (tương tự, có citations [1]–[5] trỏ tới Microsoft Learn, Taskade, Dataiku, doubleSlash blog, xCubeLabs).

### Q3: Summarize production guardrails for LLM agents

**Output baseline:** liệt kê 5 nhóm guardrail (safety, monitoring, robustness, transparency, user interaction) nhưng không có nguồn.

**Output multi-agent:** phân loại pre-LLM / post-LLM guardrails, layered approach, có citations tới Wiz, TUTAI, Arthur AI, OWASP/NIST, Datadog.

> Output đầy đủ của Q2/Q3 có trong git history trước commit này; có thể chạy lại lệnh `benchmark` để regenerate.

## 5. Trace links

Các public trace link dưới đây có thể click thẳng (không cần login LangSmith) — dùng để screenshot/nộp bài.

| Run | Public trace link |
|---|---|
| Baseline (1 LLM call) | https://smith.langchain.com/public/f6c90f0e-e95d-4e90-a0f7-dac2ef088a98/r |
| Multi-agent — Researcher | https://smith.langchain.com/public/4c17d84b-f2a7-4275-ba65-968a345c82b9/r |
| Multi-agent — Analyst | https://smith.langchain.com/public/04f84f92-5a95-46e3-af45-03341aabd977/r |
| Multi-agent — Writer | https://smith.langchain.com/public/438f687b-5952-44fd-82b2-2d6a5f3ff0c6/r |




## 6. Failure mode và cách fix

### Failure mode 1 — Search trả empty hoặc lỗi mạng
- **Triệu chứng**: Researcher không có sources → research_notes vô nghĩa → final_answer bịa.
- **Bằng chứng**: `state.errors` chứa `researcher.search: ...`; `citation_coverage` rớt về 0.
- **Fix đã làm**: `SearchClient` có fallback sang mock khi Tavily lỗi (xem [search_client.py:21-27](../src/multi_agent_research_lab/services/search_client.py#L21-L27)).
- **Fix nâng cao**: Supervisor nên route lại Researcher với query reformulated, hoặc abort và fallback sang baseline thay vì cố trả lời với 0 sources.

### Failure mode 2 — LLM rate-limit hoặc timeout
- **Triệu chứng**: agent raise `openai.RateLimitError` hoặc `Timeout` → `AgentExecutionError`.
- **Fix đã làm**: `LLMClient.complete` bọc retry exponential backoff (3 lần, 1–8s) bằng `tenacity` ([llm_client.py:75-79](../src/multi_agent_research_lab/services/llm_client.py#L75-L79)) và timeout cứng từ `settings.timeout_seconds`.
- **Fix nâng cao**: Thêm circuit breaker per-agent, fallback sang model rẻ hơn (`gpt-4o-mini` → `gpt-3.5-turbo`) khi 4o-mini fail.

### Failure mode 3 — Loop vô hạn / supervisor không bao giờ DONE
- **Triệu chứng**: iteration tăng đều, route_history dài, cost cháy.
- **Fix đã làm**: Hard cap `max_iterations` (default 6) trong cả `SupervisorAgent.decide` và `MultiAgentWorkflow.run`; cộng thêm rule "≥3 errors → DONE" ([supervisor.py:32-37](../src/multi_agent_research_lab/agents/supervisor.py#L32-L37)).
- **Fix nâng cao**: Thêm cost budget per-run; abort khi `sum(cost_usd) > budget`.

### Failure mode 4 — Hallucinated citations
- **Triệu chứng**: Writer xuất `[6]` mà chỉ có 5 sources, hoặc `[2]` không khớp nội dung.
- **Fix đã làm**: Source list được gắn rõ vào prompt của Writer; system prompt yêu cầu giữ `[n]` từ analysis. Coverage được đo trong [evaluation/benchmark.py](../src/multi_agent_research_lab/evaluation/benchmark.py) bằng regex `\[(\d+)\]`.
- **Fix nâng cao**: Bật `CriticAgent` (đã code) trong workflow loop khi `final_answer` xuất hiện, verdict = `REVISE` thì supervisor route lại Writer với feedback của Critic. Hiện workflow không gọi Critic mặc định để giữ benchmark đơn giản.

### Failure mode 5 — Cost / quality không tỉ lệ
- **Triệu chứng**: Multi-agent đắt 3.7x baseline nhưng câu hỏi đơn giản → ROI âm.
- **Fix nâng cao**: Trước khi gọi workflow, dùng 1 supervisor LLM call ngắn để classify "simple/complex"; simple → route thẳng baseline.

## 7. Hạn chế của benchmark này

- Quality score là heuristic dựa trên độ dài + có "[n]" / "Sources" — **không thay được peer review**. Số 9.0 cho multi-agent chủ yếu phản ánh "có citations + đủ dài", không phản ánh chính xác factual.
- Cost ước lượng từ `_PRICE_TABLE_USD_PER_1K` static — cần đối chiếu billing thực tế của OpenAI.
- N=3 query là quá nhỏ. Cần ≥10 query đa dạng (factual / analytical / open-ended) để kết luận có ý nghĩa.
- Chưa đo failure rate dưới load (concurrent requests, rate limit thật).
