# Regression Results

Focused canonical recovery qualification: 13 passed.

The broader related suite was first run with the candidate uncommitted; four
root-based tests correctly failed with `UNCOMMITTED_WORKING_TREE_DRIFT`.
After placing the candidate on its clean local branch, the related suite
passed 36/36.

Controlled-document validation passed 2,863 checks with 0 failures. Registry
validation passed for 87 objects. `git diff --check` passed. Platform
validation passed stages 1, 3, and 4; stage 2 correctly failed because this
candidate branch is not yet published and synchronized to EOS.

Live `resume`, dispatch, and execute were not run.
