# Related Incident Evidence · shadcn Local Demo UI

This Vite/React UI is a local presentation layer only. It sends one typed browser payload to the existing Python demo API:

```text
POST /api/triage
```

The Python application remains the sole source of typed packet creation, retrieval, policy, procedure posture, provider degradation, and representative-selection behavior.

## Local development

1. Start the Python API at `http://127.0.0.1:8765`.
2. Run `npm install` once in this directory.
3. Run `npm run dev`.
4. Open `http://127.0.0.1:5173`.

The Vite development server proxies only `/api` to `127.0.0.1:8765`.

## Safety boundary

- No browser-side policy decisions.
- No browser-side procedure eligibility or execution decisions.
- No persistence, accounts, upload flows, or connectors.
- No local storage of request payloads.
- `procedure_execution_authorized` remains owned by the packet and must remain `false`.

## Validation

```powershell
npm run test
npm run build
```
