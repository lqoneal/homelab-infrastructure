# Canonical Selection Source Map

| View | Canonical owner | Selection source |
| --- | --- | --- |
| `mission list` | `scripts.lib.eos.operational_beta.active_missions` | `_selected_card` |
| `mission queue` | `scripts.lib.eos.operational_beta.queue` | `_selected_card` via `operation` |
| `mission next` | `scripts.lib.eos.operational_beta.next_action` | `_selected_card` |
| `mission recommend` | `scripts.lib.eos.operational_beta.next_action` | `_selected_card` |
| `mission health` | `scripts.lib.eos.operational_beta.operation` | `_selected_card` |
| authority/contract/snapshot | `operational_beta.mission_view` | same mission card and projection |

The former Operational Alpha resolver remains available to its historical
commands and is not used for Beta selection.
