# DOI reconciliation — Task2B v1

All seven historical singleton DOI discrepancies were investigated against the hash-verified original proceedings cache, original OpenAlex response and two new Crossref DOI records per case. No original response was changed. No source-corrected graph was built: all seven retain ambiguous mismatch status in the identity candidate.

The returned OpenAlex work combines a proceedings title/byline/year with a later journal DOI. Crossref separately registers both DOIs, with matching titles and ordered author names but different publication dates/containers. No record deposits an explicit version relation. This is evidence of probable mixed-version provider metadata, not seven proven unrelated papers and not a verified authorship/affiliation crosswalk. Titles alone cannot authorize these matches.

New acquisition method `release-openalex-v1.1` checks requested/returned DOI equality in `evaluate_match`, including singleton retry and duplicate-record selection. `verify_work_doi` distinguishes exact DOI, explicitly reconciled equivalent version, ambiguous mismatch, incorrect match and missing source. Acquisition still accepts exact DOI only; a version ledger does not authorize transferring historical affiliations. Synthetic tests exercise the other states; none of these seven is labeled verified equivalent.

Machine ledger: [doi-ledger.json](investigation/doi-ledger.json). Public request timestamps, hashes and URLs: [external-request-ledger.json](external-request-ledger.json). Full source bytes remain ignored under `data/raw/identity-recovery-v5-release-v1/`. Official byte hashes were rechecked, rather than trusting old work logs. Original OpenAlex bytes are also rechecked by the candidate build.

## paper:aaai:2022:20425

Official: **Weighted Fairness Notions for Indivisible Items Revisited**. 10.1609/aaai.v36i5.20425; AAAI 2022. Byline: Mithun Chakraborty, Erel Segal-Halevi, Warut Suksompong.

Returned: `https://openalex.org/W4226163689`; `10.1145/3665799`; title “Weighted Fairness Notions for Indivisible Items Revisited”, provider year 2022; byline Mithun Chakraborty, Erel Segal-Halevi, Warut Suksompong.

Official cache SHA256 `f72dc72a61838ccaffeadf21e4e4e094952a87bde0ff3c40b8795c950cc23605`, locator `a[href='https://ojs.aaai.org/index.php/AAAI/article/view/20425']`. OpenAlex SHA256 `53c19435f0af1774e869b1f6b4937df98e9894bb835b350e120acf8a385e4544`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.1609/aaai.v36i5.20425`: journal-article, {'date-parts': [[2022, 6, 28]]}, container ['Proceedings of the AAAI Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `39ac0b90a8ccc96026fe09edf4c4203c7721ba9b124206b2dc461e071bbb89a1`.
- DOI `10.1145/3665799`: journal-article, {'date-parts': [[2024, 9, 6]]}, container ['ACM Transactions on Economics and Computation']; deposited relation `{}`. Source SHA256 `a37d51b77d9fb7d68b4f42e0a345ce5ce4af94992aa5d883bc006fad59671f9a`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 3 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## paper:aaai:2023:26455

Official: **Fair Short Paths in Vertex-Colored Graphs**. 10.1609/aaai.v37i10.26455; AAAI 2023. Byline: Matthias Bentert, Leon Kellerhals, Rolf Niedermeier.

Returned: `https://openalex.org/W4382203006`; `10.1016/j.tcs.2026.116201`; title “Fair Short Paths in Vertex-Colored Graphs”, provider year 2023; byline Matthias Bentert, Leon Kellerhals, Rolf Niedermeier.

Official cache SHA256 `8a23040e6bb4d3a21e94196b1636767bb7c71a88f827f78a4f6fdae3942daf63`, locator `a[href='https://ojs.aaai.org/index.php/AAAI/article/view/26455']`. OpenAlex SHA256 `e5e3dc674f6eba7d11a1a32721864ece7a0ef69fa983872c8879acf56ee84bd2`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.1609/aaai.v37i10.26455`: journal-article, {'date-parts': [[2023, 6, 26]]}, container ['Proceedings of the AAAI Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `65e6013fb187e3da56b8b90b35cc392f7d04c158dd710eebc6b347daace9eb30`.
- DOI `10.1016/j.tcs.2026.116201`: journal-article, {'date-parts': [[2026, 10]]}, container ['Theoretical Computer Science']; deposited relation `{}`. Source SHA256 `80a3879c66332fdc8f7c0d963e076fe64132d992d675ebba126e9faf36d9a2b3`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 3 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## paper:ijcai:2021:43

Official: **Strategyproof Randomized Social Choice for Restricted Sets of Utility Functions**. 10.24963/ijcai.2021/43; IJCAI 2021. Byline: Patrick Lederer.

Returned: `https://openalex.org/W3190796281`; `10.1007/s00355-026-01654-w`; title “Strategyproof Randomized Social Choice for Restricted Sets of Utility Functions”, provider year 2021; byline Patrick Lederer.

Official cache SHA256 `418ca105660be37023086c0687e3fa3cf1beb47d06fa78e38fb7dc52090ca092`, locator `a[href='/proceedings/2021/43']`. OpenAlex SHA256 `b2c110f3174b87f63045b04a618e294f69ebb19cf246bf543270946faaa3c25e`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.24963/ijcai.2021/43`: proceedings-article, {'date-parts': [[2021, 8]]}, container ['Proceedings of the Thirtieth International Joint Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `2a4f136da67c64ebc90272665a1c2f0bd5f91678ae547769b5110afea248dbc7`.
- DOI `10.1007/s00355-026-01654-w`: journal-article, {'date-parts': [[2026, 4, 17]]}, container ['Social Choice and Welfare']; deposited relation `{}`. Source SHA256 `c92da871dca45478957226bf5163a44d82b9c5efb9d403b0a7dd20aa120f8da1`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 1 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## paper:ijcai:2022:34

Official: **The Complexity of Envy-Free Graph Cutting**. 10.24963/ijcai.2022/34; IJCAI 2022. Byline: Argyrios Deligkas, Eduard Eiben, Robert Ganian, Thekla Hamm, Sebastian Ordyniak.

Returned: `https://openalex.org/W4285607100`; `10.1016/j.artint.2026.104585`; title “The Complexity of Envy-Free Graph Cutting”, provider year 2022; byline Argyrios Deligkas, Eduard Eiben, Robert Ganian, Thekla Hamm, Sebastian Ordyniak.

Official cache SHA256 `e0415ade96a76ed9bbde4c9255a976f7c2c4081e6f094991b944803b161cf4c8`, locator `a[href='/proceedings/2022/34']`. OpenAlex SHA256 `2df31c36bf682dd5f61d26dd0f7294232db3954641499670c93bf6b0478cb8f5`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.24963/ijcai.2022/34`: proceedings-article, {'date-parts': [[2022, 7]]}, container ['Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `662f09b8f59832fd5f9be181c6912f58819c82a847bf5c8adadac30b5e78f062`.
- DOI `10.1016/j.artint.2026.104585`: journal-article, {'date-parts': [[2026, 9]]}, container ['Artificial Intelligence']; deposited relation `{}`. Source SHA256 `79bde97c38c27556c6d901f5ef4b938d14559f5a7b9b62c235e9f946909b2839`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 5 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## paper:ijcai:2022:635

Official: **Online Bin Packing with Predictions**. 10.24963/ijcai.2022/635; IJCAI 2022. Byline: Spyros Angelopoulos, Shahin Kamali, Kimia Shadkami.

Returned: `https://openalex.org/W4225709049`; `10.1613/jair.1.14820`; title “Online Bin Packing with Predictions”, provider year 2022; byline Spyros Angelopoulos, Shahin Kamali, Kimia Shadkami.

Official cache SHA256 `e0415ade96a76ed9bbde4c9255a976f7c2c4081e6f094991b944803b161cf4c8`, locator `a[href='/proceedings/2022/635']`. OpenAlex SHA256 `64f3245aa8d6c10073eceff9c936200db5d5a8830142c93c73c2a3bb7fa6fc2a`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.24963/ijcai.2022/635`: proceedings-article, {'date-parts': [[2022, 7]]}, container ['Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `a926b48abf6068337e2ca6f3fdb6536164ba1e95f5e77f1b2e4e2bc58d3a8d2a`.
- DOI `10.1613/jair.1.14820`: journal-article, {'date-parts': [[2023, 12, 20]]}, container ['Journal of Artificial Intelligence Research']; deposited relation `{}`. Source SHA256 `eaaa4719703f86d9d6d9589cee6ef7fa3b26abdddce4015ad2cc6814112dd8cb`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 3 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## paper:ijcai:2025:444

Official: **Asymptotic Fair Division: Chores Are Easier Than Goods**. 10.24963/ijcai.2025/444; IJCAI 2025. Byline: Pasin Manurangsi, Warut Suksompong.

Returned: `https://openalex.org/W4414359482`; `10.1137/25m180161x`; title “Asymptotic Fair Division: Chores Are Easier Than Goods”, provider year 2025; byline Pasin Manurangsi, Warut Suksompong.

Official cache SHA256 `a2d0ca0d46b7d49ad3f4f42008ca31f256fbc49d0e33a313d8d843144b7c781b`, locator `a[href='/proceedings/2025/444']`. OpenAlex SHA256 `a77b4faf1fb0259bfab8d02bcfd51ca4bc141239d6ceb986677cb6c3863fdc4c`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.24963/ijcai.2025/444`: proceedings-article, {'date-parts': [[2025, 9]]}, container ['Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `d60065aa2fd88f3bcc9161c252eee0ed71ee7786b377e210251274330a37d743`.
- DOI `10.1137/25m180161x`: journal-article, {'date-parts': [[2026, 7, 14]]}, container ['SIAM Journal on Discrete Mathematics']; deposited relation `{}`. Source SHA256 `884c66a25f02214c2a4bba36741a79b37bb7adca4e2763f5e79936bdc2a2a50f`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 2 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## paper:ijcai:2025:446

Official: **Variety-Seeking Jump Games on Graphs**. 10.24963/ijcai.2025/446; IJCAI 2025. Byline: Lata Narayanan, Jaroslav Opatrny, Shanmukha Tummala, Alexandros A. Voudouris.

Returned: `https://openalex.org/W4414359813`; `10.1613/jair.1.21746`; title “Variety-Seeking Jump Games on Graphs”, provider year 2025; byline Lata Narayanan, Jaroslav Opatrny, Shanmukha Tummala, Alexandros A. Voudouris.

Official cache SHA256 `a2d0ca0d46b7d49ad3f4f42008ca31f256fbc49d0e33a313d8d843144b7c781b`, locator `a[href='/proceedings/2025/446']`. OpenAlex SHA256 `a102f574fb2323363b5412762a309e78e6b9fce60c24d085bc3197de1e236109`, locator `$`. Stored alternate records: 0; none supplies an exact-DOI alternate for this singleton case.

- DOI `10.24963/ijcai.2025/446`: proceedings-article, {'date-parts': [[2025, 9]]}, container ['Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence']; deposited relation `{}`. Source SHA256 `34d7b808867615884c494bcaf995e255df87a6c959d0697fdc247da0d179e3b6`.
- DOI `10.1613/jair.1.21746`: journal-article, {'date-parts': [[2026, 8, 15]]}, container ['Journal of Artificial Intelligence Research']; deposited relation `{}`. Source SHA256 `b16d23aeb8d6a983ad1e8bc5d4111bd358aeb6d72f76622c41f6da359e5ebea4`.

Decision: **ambiguous mismatch**, likely proceedings/journal version linking or canonical-provider DOI consolidation. Explicit equivalence and the source version of the authorship institutions remain unverified. Withhold 4 identity positions; retain the official paper, topics and existing citation/publication claims unchanged. Journal-only ORCIDs are not assigned to proceedings authors automatically.

## Consequences and remaining work

All 21 affected positions remain withheld, as in candidate-v3. The identity-only comparison therefore includes no DOI recovery, no corrected source and no extra journal-derived affiliation. Existing v4 citations and topics remain exact; preserving them is a scoped comparison choice, not new certification of their DOI-version semantics. An explicit publisher version statement plus proceedings-specific identity/affiliation evidence would support a separate source artifact; matching titles/bylines and an API redirect do not suffice.
