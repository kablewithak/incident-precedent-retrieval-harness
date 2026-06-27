# shadcn Local Demo Development Runbook

## Purpose

Run the React/shadcn development frontend against the existing local Python demo boundary without changing policy authority or exposing the demo beyond loopback.

## Preconditions

- Repository root is open in PowerShell.
- The existing local dense index is present at `evidence_vault/indexes/local-sie-dense-index-v1.json`.
- Node.js 22+ and npm are installed.
- The local SIE container exists.
- No public tunnel, port forwarding, or non-loopback bind is used.

## First-time frontend install

```powershell
Set-Location .\apps\local-demo-ui

npm install

npm run test

npm run build
```

`node_modules/`, Vite caches, and `dist/` must not be committed.

## Run the two local processes

Open a first PowerShell window at repository root:

```powershell
docker start incident-sie

python .\scripts\run_local_submission_demo.py `
    --repository-root . `
    --port 8765
```

Open a second PowerShell window:

```powershell
Set-Location .\apps\local-demo-ui

npm run dev
```

Open `http://127.0.0.1:5173`.

The Vite app proxies only `/api` to the Python server. The browser does not call Superlinked, retrieval, policy, or procedure code directly.

## Validation

From the repository root:

```powershell
python -m pytest .\tests\unit\test_local_demo_application.py
python -m pytest .\tests\unit\test_local_demo_ux_copy.py
```

From `apps\local-demo-ui`:

```powershell
npm run test
npm run build
```

## Stop

Use `Ctrl + C` in each process window.

## Do not do

- Do not add policy logic to React.
- Do not display a procedure as executable.
- Do not expose Vite or Python server on a network interface.
- Do not persist incident summaries in browser storage.
- Do not treat advisory SIE rank as a conclusion.
