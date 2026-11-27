# Contributing

Work should be agreed with the team before implementation. Each contributor should use their own GitHub account, work on a focused branch, and open a pull request describing and demonstrating their actual changes. Do not create commits under someone else's account or claim work you did not do.

## Suggested independent contributions

Choose a task that has not already been taken:

1. **Data validation tests:** Add tests for BHK parsing, `total_sqft` ranges and unit conversions, duplicate handling, and output row/column expectations. Include edge cases and run them against the real Phase 1 script.
2. **Model selection and validation:** Add a fair mean-baseline comparison and cross-validated comparison for all candidate regressors. Document the metric used to choose the final model and update saved artifacts from reproducible code.
3. **Prediction interface:** Build a small Streamlit form that validates the six model input features and calls the saved preprocessing/model pipeline. Include example inputs and clearly label outputs as estimates.
4. **Documentation and review evidence:** Improve the data dictionary and cleaning rationale, verify source attribution/license, and add an EDA findings report with numbers traceable to generated outputs.

## Pull request checklist

- Explain the problem and the change.
- Include focused tests or reproducible evidence.
- Do not commit credentials, private information, virtual environments, caches, or unrelated files.
- Update documentation if behavior or setup changes.
- Have another teammate review the pull request before merging.
