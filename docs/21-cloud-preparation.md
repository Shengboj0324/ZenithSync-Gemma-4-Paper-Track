# Cloud preparation for inference training and deployment

Updated October 7, 2026. Prepare access and bounded budgets now; allocate compute when the model and official harness are ready. No paid resource has been created by this implementation cycle.

| Service | Prepare now | First use and acceptance check |
| --- | --- | --- |
| Runpod | Funded account; SSH public key; experiment spending ceiling, maximum duration and storage ceiling. If using its CLI, arrange its own credential access securely; MCP authentication alone does not establish CLI access | P1: exact checkpoint load and tool-call smoke on a bounded GPU pod. P5: training/export/reload pilot. Verify SSH, transfer hashes, measured peak memory, checkpoint persistence and shutdown behavior |
| DigitalOcean | Select the project and authorized SSH public key; identify an existing suitable Linux workspace if available; set CPU-worker budget | Local Docker now satisfies R0 synthetic checks; use a remote CPU worker only when needed in P2. Verify Docker, offline dependencies, filesystem isolation and real task execution before relying on it |
| Cloudflare | Prepare a private R2 bucket, account ID, bucket name and appropriate S3 endpoint. Create bucket-scoped Object Read & Write credentials through your account; store the access key and secret securely outside Git/chat | Artifact backup and recovery. Verify a small upload/download with matching SHA-256 before transferring models or checkpoints. A public bucket, Worker and domain are unnecessary for this stage |

Live read-only verification in this cycle: Runpod pod listing succeeded, including cluster members, with an empty result and no next page. DigitalOcean account lookup succeeded and returned active status and verified email. These checks establish API authentication only; SSH, provisioning, Docker, GPU execution and training are untested. The earlier Cloudflare plugin search found no matches, and no Cloudflare account/API operation has been verified. More integrations may exist; use official S3/API credentials or a supported connection when needed.

R2 requires activation before token creation. Its S3 credentials are separate from general Cloudflare API access; scope permissions to the project bucket and use the endpoint appropriate to its jurisdiction. See [Cloudflare authentication instructions](https://developers.cloudflare.com/r2/api/tokens/).

For Runpod, keep important checkpoints on storage whose lifecycle survives the intended compute teardown, and verify an independent backup before deleting resources. Storage types have different stop/termination behavior; choose the region together with GPU availability, then quote the live compute and storage costs. See [Runpod storage documentation](https://docs.runpod.io/pods/storage/types). Hardware selection remains provisional until the actual loader, context size and training representation are known; model download size is not a VRAM requirement.

## Files and decisions needed from you

1. The official guide and starter have now been retrieved using your existing Kaggle credentials; no manual download of those is needed. Full development snapshots/task dependencies remain to be staged for real-task execution; the local synthetic sandbox already works. Keep reference fixes out of evaluation-time agent inputs.
2. Download the complete selected Gemma variation outside this repository and retain its Kaggle revision. When complete, provide its folder/archive path. We will verify files and hashes before P1 and before transfer; do not purchase a second training checkpoint yet.
3. Set a maximum spend per experiment and per month, maximum pod runtime, and persistent-storage budget. Include failed experiments and stopped-resource storage. We will specify the exact resource and live rate before allocation.
4. Make the provider credentials available through supported connectors or local secret storage; send only nonsecret paths and readiness status in chat. Keep provider credentials out of task sandboxes and submitted artifacts.

Training starts after real inference, baseline evaluation and a small adapter compatibility round trip. A packed inference checkpoint and permission to submit LoRA do not establish that direct training on that file is supported. DigitalOcean serves CPU development/evaluation; Runpod serves GPU inference/training; R2 stores recoverable artifacts. Additional hosting is optional after the core agent works.
