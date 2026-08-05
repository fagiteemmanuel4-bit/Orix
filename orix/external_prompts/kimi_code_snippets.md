Source: https://github.com/MoonshotAI/kimi-code

CLI snippets and usage (extracted):

- Install (Windows PowerShell):
  - `irm https://code.kimi.com/kimi-code/install.ps1 | iex`

- Quick start:
  - `cd your-project`
  - `kimi`
  - On first launch run `/login` inside the TUI to authenticate (OAuth or API key).

- Editor integration:
  - `kimi acp` exposes Agent Client Protocol for editors (Zed, JetBrains).

Notes:
- Kimi Code CLI is TUI-first, single-binary, and provides lifecycle hooks and plugin systems — useful patterns for `orix`'s CLI design and permission gating.
