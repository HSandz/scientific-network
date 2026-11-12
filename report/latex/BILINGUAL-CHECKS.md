# Bilingual terminology and factual checks

Review date: 12 November 2026 (+07:00). Both editions use production v4,
`release-d3c788c3114a`. The primary agent owns the integrated manuscripts,
scientific verification, compilation and visual inspection.

## Consistent terms

| English | Vietnamese used |
| --- | --- |
| Data collection / preprocessing | Thu thập / tiền xử lý dữ liệu |
| Knowledge graph / network analysis | Đồ thị tri thức / phân tích mạng |
| Entity resolution | Phân giải thực thể |
| Researcher disambiguation | Phân biệt định danh nhà nghiên cứu |
| Coauthorship / collaboration network | Mạng đồng tác giả / mạng hợp tác |
| Connected component | Thành phần liên thông |
| Degree / degree centrality | Bậc / độ trung tâm bậc |
| Betweenness centrality | Độ trung tâm trung gian |
| Community detection | Phát hiện cộng đồng |
| Citation network | Mạng trích dẫn |
| Topic classification | Phân loại chủ đề |
| Paper-specific affiliation | Liên kết tổ chức theo từng bài / đơn vị công tác có bằng chứng theo bài |
| Provenance | Thông tin nguồn gốc dữ liệu |
| Observed / inferred / curated / derived | Quan sát / suy ra từ mô hình / biên soạn / dẫn xuất |
| Pair–paper supports | Lượt hỗ trợ cặp tổ chức–bài báo |
| Abstention | Không gán nhãn khi chưa đủ chắc chắn |

Official names, titles, model names, graph predicates, IDs and URLs retain their
original form. Both editions use comma thousands separators and decimal points
consistently, making numerical comparison direct. Precision is explicitly a
prediction-positive metric, not classification accuracy.

## Evidence and meaning checklist

- Shared numerical macros and inventory/annual/centrality tables are generated
  once from pinned summary/analysis artifacts. The schema table and diagrams
  share bilingual sources. Literal-number multisets match for each overview and
  chapter pair; this is supplemented by source-text review, not used as a
  substitute for meaning checks.
- Both editions retain 13,617 official papers, 13,606 matched works, 11 unmatched
  records, 47,875 nodes, 225,731 accepted edges, and all ten relation counts.
- The 65,507 official positions, 65,469 matched positions, 50,437 accepted
  authorships and 48,259 affiliated positions have separate denominators.
  Affiliation observations are not counted as aggregate affiliation edges.
- Topic availability is 11,575/13,617 (85%); 2,042 papers abstain. Fractional
  topic shares use labeled papers and are not accuracy claims.
- Seven historical returned-DOI discrepancies remain unresolved. A subsequent
  guard does not retroactively repair v4. Experimental identity results do not
  enter either edition.
- The same 80,482 coauthor pairs, 20,776-member largest component, 2,936
  components, 414 researcher isolates, 13,031 organization pairs, 90 organization
  isolates, and approximate Bo An betweenness 0.042193 are preserved.
- Unique organization pairs differ from pair–paper supports; mirrored matrix
  cells cannot be doubled. Organization support requires two distinct authors.
- The citation projection has 7,308 edges and 7,302 isolates; Informer's 51 incoming
  citations are within-corpus only. Citation arrows go from citing to cited.
- The 193/200 source-backed review is explicitly AI-assessed, with source reuse,
  unestablished evaluator independence and no human validation. The Wilson
  interval describes sampling, not evaluator error. Historical AI topic
  references do not become an independent human test.
- Relationship directions, support thresholds, team-size weights, profile
  denominators, uncertainty and limitations agree across languages.
- All ten captions, navigation, covers, tables, axes, legends, topic labels,
  sectors and diagram annotations have language-appropriate text. Bibliography
  access notes are localized; official reference titles remain original.

## Bounded delegated reviews

All requested reviews used fresh **GPT-6-Luna** contexts with **High** reasoning,
read-only, without modifying manuscripts or data. These are report-editing
reviews, not new graph evaluations or human validation.

1. `v4_fact_review` verified frozen v4 facts and then checked the active English
   narrative, tables and accepted-edge example: no actionable factual issues.
2. `bilingual_review` checked numerical/semantic parity and Vietnamese terminology.
   Corrections clarified micro precision, the absence of an independent human
   topic test, explicit lack of human validation, the 20,776 separator, and
   paper-specific affiliations. Primary agent integrated those corrections.
3. `final_bilingual_check` reviewed all active overview/chapter sources, shared
   tables/diagrams and plot translations. It confirmed the earlier corrections,
   relation directions and support semantics. It identified one remaining
   unqualified Vietnamese phrase about an incorrect edge. This now reads
   “một trường hợp được đánh giá là sai”, preserving its status as a judgment.
   Two optional clarity improvements were also applied: researchers **per
   component** in the plot axis and the full betweenness metric name in the table.

The primary agent checked the final edits and reran automated verification.
The last delegated review was a source comparison; rendered glyph/layout review
was performed separately by the primary agent. No additional subagent signoff
after those final three small edits is claimed.

See [REVIEW-BILINGUAL.md](REVIEW-BILINGUAL.md) for build, typography, full-page
visual inspection and remaining submission fields.
