# 00_MANIFEST — WRITING_PACKAGE

**Assembled 2026-08-10 from repo state `main@2b1413b` (laptop + server synced; raw data authority: server mount `/data5/kje/MULTIAGENT/DACS-AUQ`).**

## Validation summary (§7 of the handoff)

1. Cross-references: 131 registry rows; every num_id referenced by a brief/table/figure exists; zero orphans; zero dangling references.
2. Spot check: 25 random registry rows verified against their source artifacts token-for-token (2 initial flags were checker tokenization artifacts, re-verified clean).
3. Ledger consistency: T11/T16/F7 verdict strings assembled from `FINAL_BUNDLE/GATES_LEDGER.md` and the gate summaries; no verdict deviates from the ledger.
4. Both-label-pass rule: L1 rows carry L2 counterparts where they exist; L1-only analyses are flagged as defect item 9 in `06_GAPS.md`.
5. `06_GAPS.md` is non-empty: 5 gaps, 3 conflicts of record, 1 label-pass defect class, 1 untracked-inputs note.

## Package files (sha256 of each file in this package)

- `01_NUMBERS_REGISTRY.csv` — `9647642f57febb73ab4b0dc1832adf06ab7f6a29305d358ec437244ba6c6e59f`
- `02_SECTION_BRIEFS/S1_intro.md` — `d5ed9de7330dcbdc1bcc5314c62a599d61f006861a4938113ab13c85c6f71a26`
- `02_SECTION_BRIEFS/S2_related.md` — `359c1a35573800bf7014bd0b005986f55035b33bf49aa4376a5c80c37fb4e5e8`
- `02_SECTION_BRIEFS/S3_problem_setup.md` — `db3771bea0729a7633d0099c1e5e871cc8029ca6793969813eeea362b758cf63`
- `02_SECTION_BRIEFS/S4_impossibility.md` — `636683cbddbbb81ecc613062e01bf7d389ebe8d7502292661d2c4b1419d73a3f`
- `02_SECTION_BRIEFS/S5_independence.md` — `81bf48bd658930889847f732c86a21c97e7dd569886d1bcfc6cc3990aefd2f8b`
- `02_SECTION_BRIEFS/S6_instrument.md` — `c990facba30ed8eba0b557f5adf2a0455df5d37469abd28355a2eece94383005`
- `02_SECTION_BRIEFS/S7_deployment.md` — `3e58707309b35d534950ecf3eb1fb50f2ba6ac96867175ee7a7a5150e64923c4`
- `02_SECTION_BRIEFS/S8_mechanism_and_limits.md` — `b8441afd0aa16de253969a9142b0011727ca1e0ac7c41db60f087dcb0b6fa862`
- `02_SECTION_BRIEFS/S9_appendix.md` — `266370637f02c7db89b60083902bf00b118209affe86ef9646e81cd5d2ff0603`
- `03_TABLES/T10_label_source_menu.csv` — `1ec3c864a3e780a41870c8f1e4dabec3dbab67d20810712a5726a6b373b6ed15`
- `03_TABLES/T10_label_source_menu.md` — `8e125a668fe1f58a923fedfad70f00cab900e1fd802a2f9b56af1bec551b5908`
- `03_TABLES/T11_h_arc_verdicts.csv` — `de78a2d7968227cabe3bdf514f9691cabc1eff13e977529d2680986ccd4e4e9a`
- `03_TABLES/T11_h_arc_verdicts.md` — `6a8dfda9d7efc2f352fadedee89cfa705ab0fc4609eb113e1d9e59e5626aa1ba`
- `03_TABLES/T12_gate4_partA_per_cell.csv` — `cb60902b501715d20a3bd53f4ec8405cce4ece8b1a1ae39e1a392c417ae6a2a8`
- `03_TABLES/T12_gate4_partA_per_cell.md` — `e82f9b67760ec07ae629c6139cdb42d1bf02394582521d6871feb0bb685532af`
- `03_TABLES/T12b_partA_full_evaluation.csv` — `4a7214daa6c20f566c77486ce9a46c041dfd4ddd6a21dae5fdb43165f709ed7a`
- `03_TABLES/T12c_gate4_27B_extrapolation.csv` — `081822b31f97b45bae416ab0a3bdc16b8bb08fadb7d6983293cbea3cc231a18c`
- `03_TABLES/T13_partB_invariance.csv` — `fd60062336a7682223ee510cd3748f240a6cd66dffec245358a817c269bbffda`
- `03_TABLES/T13_partB_invariance.md` — `bb6b208aaf8ea031a31419b213eca88ea0ee9ea2453dd4736cd7dccf8eb97d53`
- `03_TABLES/T14_partC_stability.csv` — `4bfa5a367ea717a7ad707cf488eb9ee51908f6f533327f56daefbc3d4e4e31cc`
- `03_TABLES/T14_partC_stability.md` — `bce067658ba2f48f527a583a31f596eaa46cef5e07758d9c477e4cbdc55725d9`
- `03_TABLES/T14b_partC_jackknife_swings.csv` — `1868bafa57d6f725dff6e2b8ed58d2af7c78b270f5064118cd994925dbe882f6`
- `03_TABLES/T15_s8_floors.csv` — `23c562c75632b716e89bef820a27594a1a41221ea7e2c2a7f4f554c62eac8886`
- `03_TABLES/T15_s8_floors.md` — `988974cf0cbd1ede514eb156af184aa12eae5badffb11fa92001e9cab6473a87`
- `03_TABLES/T16_gate1_and_circularity.csv` — `2c44817a33ea8add21c83202b365c6e09fc6b02c2a0a654e51687c2b3799dcac`
- `03_TABLES/T16_gate1_and_circularity.md` — `b540dc667d42b3e2891ade2da812ac2418d6206bebe133d73d1aa558517d7b33`
- `03_TABLES/T17_corpus_datasheet.csv` — `6a5bc3d097138575e29c609bf2784f8ff91c924e659cd4496abf7da523879407`
- `03_TABLES/T17_corpus_datasheet.md` — `2ae9d567eaa4a4b9edc83697707ee452dd364c199e9834ecc95f6f752d9bf531`
- `03_TABLES/T1_punchline.csv` — `a2fa29276bfcc4f79b2855c93cf4392c358029930a4c8e442c9df1dadefc74ec`
- `03_TABLES/T1_punchline.md` — `6268a58d8dadaf35f815f9e880c270b6058bf9563e3ceb40a3671216f54dc974`
- `03_TABLES/T2_independence_deltas.csv` — `4d46df7a6baf5ad1a3c26f39adf31771c1248e25c8424deb5de927cc075e2165`
- `03_TABLES/T2_independence_deltas.md` — `6fd007ce80abf7661a976d05c9f3cfac811a000d186491a9065576ade38df5dc`
- `03_TABLES/T3_per_arm_best_self_metric.csv` — `98817db5657e460175b4798431ab2a6d0668ab21910bad7054c41afbb81c8fce`
- `03_TABLES/T3_per_arm_best_self_metric.md` — `051e3ffcba5bd70c7e70e8ca420aeb1623a1c42f0ae22ccfb3fa57e193258c30`
- `03_TABLES/T4_fixed_scope_ladder.csv` — `f06a8001adf173b7643580e98a8b5108dcc21acad3d99417ba29a012e9cdf6b7`
- `03_TABLES/T4_fixed_scope_ladder.md` — `2014b3db20e0ac50d8f1b5003e5c2fd578d58ab3ea790552187cfaac83f80cab`
- `03_TABLES/T5_evidence_grid.csv` — `1f651ac2b17be60b15ac2f94744fa44da93d42bb201a858e073bc252fe84d809`
- `03_TABLES/T5_evidence_grid.md` — `33fe7a93eee310628892c623e58008df7e74fb517ec2655c2d5ee996b8e55439`
- `03_TABLES/T6_verdict_vs_value.csv` — `61427a7fba1506e913ee5cfdc4ed87ea6a61e1b34312e7c83a21faf923a87a7a`
- `03_TABLES/T6_verdict_vs_value.md` — `89bf6681ed39a460436a6c1b60fa29707bad1f2e25baf6a1be88842f13b3b09c`
- `03_TABLES/T7_adaptivity.csv` — `80aa0c014c7a045c37468fbdb025e98d3dc42a58357ccecc00b6314d7a8470d7`
- `03_TABLES/T7_adaptivity.md` — `c4d33e9da7d1bd83955d5cffec005dd5d095bf95346ceca68d336fc15934170c`
- `03_TABLES/T8_tier_contrast_per_cell.csv` — `20a0cfaefbbae3b07bff1edc52ecacd4a9f649e487aca50208b5e66ca3efb242`
- `03_TABLES/T8_tier_contrast_per_cell.md` — `a3ebac9fa923f0f1f3e9926cf3d0135af34041bb1d5c20c386c5c378b3fe0d4f`
- `03_TABLES/T9_frontier_per_construct.csv` — `3780560fb93865168814086e7d454d7fb30e345efb55af1c68dc442f16b64b4a`
- `03_TABLES/T9_frontier_per_construct.md` — `0e7d64c5815e6a79f32f0675affb462de249ae5dd1727b161b8f7d319bb6bf62`
- `03_TABLES/T9b_frontier_per_cell.csv` — `8dcb14d379de471b669f2dcc775dcbf0e06cb7e7b11f7c725adc2afff3068f17`
- `03_TABLES/T_extra_S71_prequential_h.csv` — `41826d47c2d347d5133e972be6dca664f7da430c403dd2f739c9d5a55dd76bf2`
- `04_FIGURES/CAPTIONS.md` — `ecee28649a7cdda8b48fd8b1620185c5007c455b86987d6044f86c595c31a3f8`
- `04_FIGURES/F1_verdict_vs_value_cells.csv` — `0b98392f6c92399bec77e13e8993b94980b06efd705091086afca12e209a3597`
- `04_FIGURES/F2_flatness_curves.csv` — `1059dd9a922d84d22010e0bf3a37be2bbfa20bf6633ea929757bed01f6e0f268`
- `04_FIGURES/F3_partB_wasserstein_pairs.csv` — `de087cf0cc2bb0e44491efe2f6095c0ab38d2b446aed8bccdddec5bf9f9b9802`
- `04_FIGURES/F4_prequential_curves_violation-judgment.csv` — `c6c59b132c88bf255abd6dbccbac35c47df3fb1086084164a81a67daabb31753`
- `04_FIGURES/F4b_prequential_curves_judgment.csv` — `7357b2aacc5543d4f72f1cf8adcec92ebdd1f6e3438892441f5f47623d3651a5`
- `04_FIGURES/F5_forecast_pi_data.csv` — `4a7214daa6c20f566c77486ce9a46c041dfd4ddd6a21dae5fdb43165f709ed7a`
- `04_FIGURES/F6_evidence_grid_ladder.csv` — `1f651ac2b17be60b15ac2f94744fa44da93d42bb201a858e073bc252fe84d809`
- `04_FIGURES/F7_h_arc_timeline.csv` — `58f9894ad8eaab7c624faa27db5c8dc37878081076467915a699ba34bf631f83`
- `05_VERBATIM/a30_construct_definitions.md` — `d95725c516a4a06b3d23dc24657489386003397fb0d755a31f909ec99a4539d8`
- `05_VERBATIM/a32_limitation.md` — `48d7927577c546ca69d18d73d4ba3437848c259fe170f7e9f4486427342b36d5`
- `05_VERBATIM/b3_deviations.md` — `abc9b20fefb4764cb2ec544e003604316b2201d648218ec834a3a00be4ad0b54`
- `05_VERBATIM/closed_questions.md` — `9b7215efe1f15d1762731a9a9cfd3c9571dd46e7b42aebb3adaeff9aa2eee6eb`
- `05_VERBATIM/gate4_closure.md` — `4b25b1f8e4a2545adcb9e589797ec4e7adc0d07e56ce3e5a62bc36768335dda3`
- `05_VERBATIM/label_trio_disjointness.md` — `f5d9de0a985c3225de1de833d662ef750fd0e4b5983183d962f96eb380149a95`
- `05_VERBATIM/partD_noclaim.md` — `45e185fb10006efb4be0e83426cea000491a91a3eb1924f2193e921167f978cc`
- `05_VERBATIM/s4_postmortem.md` — `b84678f63b8f5c5b0afa2abe047a508fde0b59708c8507d13ba52d11b09590b9`
- `05_VERBATIM/s8_signature.md` — `b9ef1c1079ace9c471f3b8ab850edf89ca8294a5609c6655655d4a74032a3945`
- `05_VERBATIM/scope_conditions.md` — `b3c5312deac0f718a3d89b359dd25a9fc9c2761fb4c2ff732f54acd8e7729bfb`
- `05_VERBATIM/seal_defect.md` — `8076f460e27b039df22762c23a4a1332ca059a24b27c5e81da6c1b3a8676a9b5`
- `06_GAPS.md` — `37d7a0e3ea9a3028924406154140097a4c8a4ad2a7a125446ca10d72936a1c43`

## Source artifacts (repo path → sha256 as read at assembly)

- `FINAL_BUNDLE/GATES_LEDGER.md` — `9d1e56dc4a8be7b848aeacb2245a5fe8be8cddb3e2dceec38245ae403f49d4dc`
- `FINAL_BUNDLE/OPEN_DECISIONS.md` — `1bb5819fff62afaa9200521dfd70dff225c26ff176e147e95585257da965117d`
- `FINAL_BUNDLE/WORDING_DEBTS.md` — `b7a9a92c68671c159229c210b0937ae8c7984490fe6606a9e031a1d916277f11`
- `FINAL_BUNDLE/claim_evidence_map.csv` — `a8213c26c4dcccf543823806f7e230f3697e34b3534d7f240a0d4d954aeb6668`
- `GATE3_SUMMARY.md` — `8b58d0b42c616f1031e4b55f7fbc9248e38b9b7af23ed0e03dd77e9e6a796d69`
- `GATE4_BCD_PARTIAL.md` — `8bafe1aba219af2ea65c209640d7b2f8ad77de38a2d3e6d64ef1699e2766ed1d`
- `GATE4_SUMMARY.md` — `02b221d78b44ba3af37315f9c2614612e8b325432e42a3e7caf95207f637d640`
- `P3_SUMMARY.md` — `a3417a801be9b1d8ad812277a657015886fbddaa9094f4ab23271e77a4dee90d`
- `S0_SUMMARY.md` — `2c30a87adf2a26a1ddb2bf1768ddafb38cae994835fb4c9ea33de372438336b0`
- `S1_SUMMARY.md` — `54da8dbb666998533fad414c56f2967e0d2ae817aa652912e900f4c2a4af6188`
- `S2_SUMMARY.md` — `9234c96ba71c2bead07e0554eacd5b4727500d3fca5ba90e5ea034f6854cf769`
- `S4_COST.md` — `cf0e8a27de566832654e9ae0a253d8c9aa9e548379e0b66f6e6760b0bf5544a8`
- `S5_BUDGET_MEASURED.md` — `83f8a9580d66eaf94b0bcf5e11b8924d5cc5951d8fbce35807a154332e548a19`
- `S5_SUMMARY.md` — `2c2683874d7612591c1a9f02ed6c4f54956cac37f8c98ba884c7913f99d61391`
- `S7_SUMMARY.md` — `28d26f60c451222c2b3e850f05d2323c5d797148cb4612e5e458dd1dbd9d4ab1`
- `S8_CRITERIA.md` — `c5a32162e9d3516bd9bb54e03cd24dcf9a33ad06ff104eb1890dcc4ad79a0360`
- `STOP_GATE_DECISIONS.md` — `d5a6bbbcaa8519e1f332278f8f1268c2e8539206f5bbe6f6e30e06fd4e8c3606`
- `analysis/answer_tripwire.py` — `06c6ce88108849f23cbe49291d7799ec9aa225a3e18637ce434de0bc05c81027`
- `docs/paper_proposal_v4.md` — `b9be6206f26385b614dea9cd187680b5ae418586f0ab5ff6c96c5062ff9e4243`
- `figures/figures_gate2b1/flatness_curves_AGG-true.csv` — `1059dd9a922d84d22010e0bf3a37be2bbfa20bf6633ea929757bed01f6e0f268`
- `labelfree_transfer_explainer.md` — `773ee91a5bbe1805cd8ac05f780f331c72ecba056de7de7fac7aa3fb907425b4`
- `reports/A30_label_constructs.md` — `dcb7f9d92a23be77b27400d48081f601294a9425ac050fbefb8e26da69688ca6`
- `reports/OPERATING_POINT_REPORT.md` — `7d36264e08315a205cc60b5dde1123ca3faf396749efe029b9d2cf6c032e9994`
- `reports/gate1/GATE1_SUMMARY.md` — `8a43f785ff421f2268efaaacf9f4dff603153147b89ec9b99e6012721802529a`
- `reports/gate1/report_phase2_ensemble_audit.md` — `3eea1cbc7515a6bf978efa74ca70770e0caf4100c29c51b32557b148aca6354e`
- `reports/gate2/GATE2B1_SUMMARY.md` — `d65391feb59f2cb0d6c18408af5e5ff308326642aa433e5e1b7306f9169a3f5d`
- `reports/gate2/GATE2B_SUMMARY.md` — `265d53a22d332ef74c9d55a2a694ef51395d3e80111d8f71ef10fd249bf38bf1`
- `reports/report_gate2_score_vs_verdict.md` — `3df35c4e7fa7b5708dcc724b98d944d438c692de75de73629860c9c6b552d5ff`
- `reports/report_online_labelfree_rule.md` — `c382a917b5fc2537f6d61f24e82604c1dd8a7df228fc49e04cebe93fbf16abc9`
- `reports/results_report_2026-08-05.md` — `e1c679d9fd448b497999e597a30cb5109bd8b4c0a3d50134b658cc41acd260eb`
- `reports/tables/verdict_vs_value.csv` — `0b98392f6c92399bec77e13e8993b94980b06efd705091086afca12e209a3597`
- `runs/manifest.json` — `20d4f23f63553350ad38c9dc0ef8db53c4d13bb4298f81f13b815072e465ac8e`
- `spotcheck/INSTRUCTIONS.md` — `f476bb93b3d91ce463f549fa9778837084ccadceb0e394ffadce602be380196e`
- `tables_P3/S71_prequential_h.csv` — `41826d47c2d347d5133e972be6dca664f7da430c403dd2f739c9d5a55dd76bf2`
- `tables_S1/S1b_independence_L2_judgment.csv` — `7ee2296183639bb31d77e8a442ce0a0487ccf9b9bb117a2bc8a6a5c01e6e1468`
- `tables_S1/S1b_independence_L2_outcome.csv` — `a4c278a9042bfce15911649c2879263a278ca075812e9708539b06f6d32a1538`
- `tables_S1/S1b_independence_L2_violation-judgment.csv` — `9a17eb036768db532e37427b9c1d02723b80b7f132f0e913f5c6f3023ea8c162`
- `tables_S1/S1b_independence_L2_violation.csv` — `0953824ee591e68e9a38cb4e97674eb21f27e99598ad7788eff9e3ba9d0ce37e`
- `tables_S1/S1b_independence_L2_y_env.csv` — `bf8c8fa25c30d3b3abe7676d5aa5e2c30a529b83c8433e5baeabd36db4c3d164`
- `tables_S5/S5_frontier_vs_open.csv` — `8dcb14d379de471b669f2dcc775dcbf0e06cb7e7b11f7c725adc2afff3068f17`
- `tables_S7/S7_curves_judgment.csv` — `7357b2aacc5543d4f72f1cf8adcec92ebdd1f6e3438892441f5f47623d3651a5`
- `tables_S7/S7_curves_violation-judgment.csv` — `c6c59b132c88bf255abd6dbccbac35c47df3fb1086084164a81a67daabb31753`
- `tables_bundle/ci_registry_final.csv` — `1c79257bf39108514462da2a284a2c83e8ec613cd9e146de5a0cae2043a11d2a`
- `tables_bundle/label_source_menu.csv` — `1ec3c864a3e780a41870c8f1e4dabec3dbab67d20810712a5726a6b373b6ed15`
- `tables_gate4/A_forecast_evaluation.csv` — `4a7214daa6c20f566c77486ce9a46c041dfd4ddd6a21dae5fdb43165f709ed7a`
- `tables_gate4/B_invariance_verdict.csv` — `fd60062336a7682223ee510cd3748f240a6cd66dffec245358a817c269bbffda`
- `tables_gate4/B_wasserstein_pairs.csv` — `de087cf0cc2bb0e44491efe2f6095c0ab38d2b446aed8bccdddec5bf9f9b9802`
- `tables_gate4/C_fit_stability.csv` — `4bfa5a367ea717a7ad707cf488eb9ee51908f6f533327f56daefbc3d4e4e31cc`
- `tables_gate4/C_jackknife_swings.csv` — `1868bafa57d6f725dff6e2b8ed58d2af7c78b270f5064118cd994925dbe882f6`

## Server-only inputs (not in this package; read over the `lg` mount)

- `result/pivot/` (50G raw score corpus incl. `crossprobe/`), `result/b3/` (frontier arm raw + `b3_sample.csv`), per-judge raw dirs — provenance only, never copied into the package.
- `S4_SUMMARY.md` (untracked, server) — NOT of record (A35 void); see 06_GAPS item 6.
