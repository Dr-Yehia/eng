# Integrated Risk v2.1 Patch — Validation

- PASS — source_manifest_present
- PASS — historical_frozen_copy
- PASS — case_role_fields
- PASS — e7q32_marked_sensitivity
- PASS — confidence_downgraded_lt3_bidders
- PASS — risk_direction_present
- PASS — action_distinguishes_over_under_ls
- PASS — rich_api_schema
- PASS — excel_new_sheets
- PASS — ml_supporting_only
- PASS — honest_no_fraud_claim

**ALL PASS = True**

## Changes
- Source manifest + frozen historical file (data/sources/).
- case_role / bidder_count / bidder_count_confidence; E7Q32 = sensitivity.
- Confidence downgraded when bidder_count<3.
- recommended_action distinguishes overpricing / underpricing / lump-sum.
- Rich API schemas (type/description/nullable/allowed/example).
- Added Excel sheets: 16_Source_Manifest, 17_Case_Role_Sensitivity, 18_Overpricing_vs_Underpricing.
- ML supporting only; wording stays abnormal pricing risk (no fraud).
