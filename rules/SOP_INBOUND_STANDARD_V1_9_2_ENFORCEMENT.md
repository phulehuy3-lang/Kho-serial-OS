# SOP v1.9.2 prospective evidence enforcement

Search zero is not missing. Recovery checks current attachments, project path,
time-window inventory, visual inspection, historical identity, hash comparison,
and canonical lookup. An exhaustion flag alone cannot authorize a missing-evidence HOLD.

G1A recovers candidates. G1B requires a Library identity and SHA-256 computed
from supplied bytes. G1C requires canonical identity and equal provider read-back
bytes. Archive defaults are false. All results deny production inventory authority.
The disposable workflow writes only a list marker after G1A/G1B/G1C. It does not
implement or bypass remaining warehouse gates, acquisition APIs, HOLD propagation,
IAM, credentials or live reads. Stage receipts remain caller-supplied offline
inputs; provider acquisition and a production workflow are not certified here.

One active recovery root is required. Prior false closes, manual gates and
prewrite misses remain immutable historical defects. Post-close fail-closed proof
cannot retroactively establish original outbound source-rank PASS or CLEAN_PASS.

Public tests use synthetic bytes only. The original PX fixture remains private;
its offline byte hash and recovery ordering are separately checked. No business
data or original evidence bytes are published.
