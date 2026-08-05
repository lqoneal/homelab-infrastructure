# Terminal Successor Root Cause

`resolve_for_start` treated the first successor as permanently terminal and raised `successor admission baseline is stale` when its baseline differed from current `main`. `resolve_for_resume` had the equivalent stale-terminal failure after traversing the chain.

