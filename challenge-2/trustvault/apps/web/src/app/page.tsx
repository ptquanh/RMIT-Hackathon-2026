"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";
const SESSION_KEY = "trustvault.demo.identity";

type Json = Record<string, any>;
type DemoPrincipal = {
  id: string;
  displayName: string;
  organizationId: string | null;
  roles: string[];
};
type IdentityMap = Record<string, DemoPrincipal>;

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function api(path: string, actor: string | null, init?: RequestInit) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (actor) headers["x-demo-user"] = actor;

  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers ?? {}) },
  });
  const body = await response.json();
  if (!response.ok) {
    throw new ApiError(body.message?.message ?? body.message ?? body.error ?? `HTTP ${response.status}`, response.status);
  }
  return body;
}

function money(value: string | number | bigint) {
  return `${BigInt(value).toLocaleString("vi-VN")} ₫`;
}

function shortHash(value?: string) {
  if (!value) return "Not frozen";
  return `${value.slice(0, 18)}…${value.slice(-10)}`;
}

export default function HomePage() {
  const [identities, setIdentities] = useState<IdentityMap>({});
  const [actor, setActor] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [dashboard, setDashboard] = useState<Json | null>(null);
  const [request, setRequest] = useState<Json | null>(null);
  const [preview, setPreview] = useState<Json | null>(null);
  const [result, setResult] = useState<Json | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("Sign in with a demo identity to begin.");

  const principal = actor ? identities[actor] : undefined;
  const hasRole = (...roles: string[]) => Boolean(principal?.roles.some((role) => roles.includes(role)));

  useEffect(() => {
    api("/demo-identities", null)
      .then((data) => {
        setIdentities(data.identities);
        const saved = window.localStorage.getItem(SESSION_KEY);
        if (saved && data.identities[saved]) setActor(saved);
      })
      .catch((error) => setNotice(`API unavailable: ${error.message}`))
      .finally(() => setAuthReady(true));
  }, []);

  const loadDashboard = useCallback(async () => {
    if (!actor) return;
    setDashboard(await api("/dashboard", actor));
  }, [actor]);

  const loadRequest = useCallback(async (id: string) => {
    if (!actor) return;
    const data = await api(`/funding-requests/${id}`, actor);
    setRequest(data.request);
  }, [actor]);

  useEffect(() => {
    if (!actor) return;
    loadDashboard().catch((error) => setNotice(`API unavailable: ${error.message}`));
  }, [actor, loadDashboard]);

  const run = async (label: string, action: () => Promise<void>) => {
    setBusy(true);
    setNotice(label);
    try {
      await action();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  const signIn = (identity: string) => run("Establishing a simulated session…", async () => {
    const session = await api("/auth/me", identity);
    window.localStorage.setItem(SESSION_KEY, identity);
    setActor(identity);
    setNotice(`Signed in as ${session.principal.displayName}. Claims came from the API demo identity map.`);
  });

  const signOut = () => {
    window.localStorage.removeItem(SESSION_KEY);
    setActor(null);
    setDashboard(null);
    setRequest(null);
    setPreview(null);
    setResult(null);
    setNotice("Signed out. No protected API identity is active.");
  };

  const createAndPreview = () => {
    if (!actor) return;
    return run("Creating a purpose-bound request…", async () => {
      const created = await api("/funding-requests", actor, {
        method: "POST",
        body: JSON.stringify({
          category: "MEDICAL",
          amount: "12000000",
          recipientRef: "hospital-demo-01",
          verificationComplete: true,
        }),
      });
      const id = created.request.id;
      const matched = await api(`/funding-requests/${id}/preview`, actor, { method: "POST" });
      setPreview(matched);
      await loadRequest(id);
      setNotice("Preview found three eligible contributions. No funds are reserved yet.");
    });
  };

  const submit = () => {
    if (!request || !actor) return;
    const requestId = request.id;
    return run("Freezing canonical payload and reserving funds…", async () => {
      await api(`/funding-requests/${requestId}/submit`, actor, { method: "POST" });
      await Promise.all([loadRequest(requestId), loadDashboard()]);
      setNotice("Payload frozen. Every approval now binds to this exact digest.");
    });
  };

  const approve = () => {
    if (!request || !actor) return;
    const requestId = request.id;
    return run(`Recording approval for ${principal?.organizationId ?? "unknown organisation"}…`, async () => {
      await api(`/funding-requests/${requestId}/approvals`, actor, {
        method: "POST",
        body: JSON.stringify({ decision: "APPROVE" }),
      });
      await loadRequest(requestId);
      setNotice("Application approval recorded against the frozen payload hash.");
    });
  };

  const tamper = () => {
    if (!request || !actor) return;
    const requestId = request.id;
    return run("Attempting recipient tamper…", async () => {
      const response = await api(`/funding-requests/${requestId}/tamper-demo`, actor, {
        method: "POST",
        body: JSON.stringify({ recipientRef: "attacker-wallet" }),
      });
      setResult({ kind: "denied", ...response });
      setNotice("Denied: changing the recipient invalidated the application approval digest.");
    });
  };

  const authorize = () => {
    if (!request || !actor) return;
    const requestId = request.id;
    return run("Checking application simulation quorum…", async () => {
      const response = await api(`/funding-requests/${requestId}/authorize-simulation`, actor, { method: "POST" });
      setResult({ kind: "simulation", ...response });
      setNotice("Simulation check passed. This is not a Tide/Forseti signature.");
    });
  };

  const settle = () => {
    if (!request || !actor) return;
    const requestId = request.id;
    return run("Sending to isolated simulation gateway…", async () => {
      const response = await api(`/funding-requests/${requestId}/settle-simulation`, actor, { method: "POST" });
      setResult({ kind: "receipt", ...response });
      await Promise.all([loadRequest(requestId), loadDashboard()]);
      setNotice("Simulation receipt recorded exactly once. No real funds moved.");
    });
  };

  const testForbiddenAccess = () => {
    if (!actor) return;
    return run("Calling a server route that this identity is not allowed to use…", async () => {
      try {
        if (hasRole("beneficiary")) {
          await api("/funding-requests/access-check/approvals", actor, {
            method: "POST",
            body: JSON.stringify({ decision: "APPROVE" }),
          });
        } else {
          await api("/funding-requests", actor, {
            method: "POST",
            body: JSON.stringify({
              category: "MEDICAL",
              amount: "1",
              recipientRef: "access-check-only",
              verificationComplete: true,
            }),
          });
        }
        throw new Error("Unexpectedly allowed: the server role policy did not deny this action.");
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 403) throw error;
        setResult({ kind: "access", status: 403, reason: error.message });
        setNotice("403 verified: the API denied the action using its server-owned role mapping.");
      }
    });
  };

  const allocationTotal = useMemo(
    () => preview?.allocations?.reduce((sum: bigint, item: Json) => sum + BigInt(item.amount), 0n) ?? 0n,
    [preview],
  );
  const currentOrgAlreadyApproved = Boolean(
    principal?.organizationId && request?.approvals?.some((item: Json) => item.signerOrgId === principal.organizationId),
  );

  if (!authReady) {
    return <main className="authPage"><p className="eyebrow">TrustVault</p><h1>Loading simulation identities…</h1></main>;
  }

  if (!actor || !principal) {
    return (
      <main className="authPage">
        <div className="authIntro">
          <div className="brand authBrand"><span className="brandMark">TV</span><span>TrustVault</span></div>
          <p className="eyebrow">TideCloak-ready authentication boundary</p>
          <h1>Choose a demo identity.</h1>
          <p>
            This screen simulates sign-in while the TideCloak realm is unavailable. The browser sends only an
            identity key; the API owns the role and organisation mapping and enforces every protected route.
          </p>
          <div className="authWarning"><span /> Simulation only · No Tide token, doken or cryptographic proof</div>
        </div>
        <div className="identityGrid">
          {Object.entries(identities).map(([key, identity]) => (
            <button key={key} className="identityCard" disabled={busy} onClick={() => signIn(key)}>
              <span className="identityAvatar">{identity.displayName.charAt(0)}</span>
              <span><b>{identity.displayName}</b><small>{identity.organizationId ?? "No organisation"}</small></span>
              <em>{identity.roles.join(", ")}</em>
            </button>
          ))}
          {!Object.keys(identities).length && <p className="statusLine">{notice}</p>}
        </div>
      </main>
    );
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="TrustVault home">
          <span className="brandMark">TV</span>
          <span>TrustVault</span>
        </a>
        <div className="sessionBar">
          <div className="modePill"><span /> Simulation · Tide not connected</div>
          <label className="identitySelect">
            <span>Signed in as</span>
            <select
              value={actor}
              onChange={(event) => signIn(event.target.value)}
              aria-label="Switch demo identity"
              disabled={busy}
            >
              {Object.entries(identities).map(([key, identity]) => (
                <option key={key} value={key}>{identity.displayName}</option>
              ))}
            </select>
          </label>
          <button className="signOut" onClick={signOut}>Sign out</button>
        </div>
      </header>

      <section className="identityStrip" aria-label="Current simulated authorization context">
        <div><span>Session</span><b>Simulated</b></div>
        <div><span>Role claim</span><b>{principal.roles.join(", ")}</b></div>
        <div><span>Organisation claim</span><b>{principal.organizationId ?? "none"}</b></div>
        <div><span>Authority source</span><b>API demo map</b></div>
      </section>

      <section className="hero" id="top">
        <div className="heroCopy">
          <p className="eyebrow">Covenant transactions</p>
          <h1>Fund the purpose.<br /><em>Not the middleman.</em></h1>
          <p className="lede">
            Independent funders can combine restricted contributions for one exact outcome—without giving
            any single organisation unrestricted authority over everyone&apos;s trust.
          </p>
          <div className="heroActions">
            <button className="primary" disabled={busy || !hasRole("beneficiary")} onClick={createAndPreview}>Start the 12M demo</button>
            <a className="secondary" href="#security">See the trust boundary</a>
          </div>
          {!hasRole("beneficiary") && <p className="roleHint">Switch to the beneficiary identity to create a request.</p>}
        </div>
        <div className="constraintCard">
          <p className="cardLabel">The trust bottleneck</p>
          <div className="network">
            <span>Fund A<br /><b>Medical only</b></span>
            <span>Fund B<br /><b>Max 5M/request</b></span>
            <span>Fund C<br /><b>Verify first</b></span>
            <div className="networkCenter">12M<br /><small>MEDICAL</small></div>
          </div>
          <p className="constraintText">Three organisations. Three conditions. No universal override key.</p>
        </div>
      </section>

      <section className="stats" aria-label="Vault summary">
        <Stat label="Committed" value={dashboard ? money(dashboard.totals.committed) : "—"} />
        <Stat label="Available" value={dashboard ? money(dashboard.totals.available) : "—"} />
        <Stat label="Reserved" value={dashboard ? money(dashboard.totals.reserved) : "—"} />
        <Stat label="Tide proof" value="Not verified" warning />
      </section>

      <section className="workspace">
        <div className="sectionHead">
          <div><p className="eyebrow">Live vertical slice</p><h2>One request, exact conditions</h2></div>
          <p className="statusLine" role="status">{busy ? "Working · " : ""}{notice}</p>
        </div>

        <div className="flowGrid">
          <article className="panel requestPanel">
            <div className="panelHead"><span className="step">01</span><h3>Funding request</h3></div>
            <dl className="detailList">
              <div><dt>Purpose</dt><dd>Emergency medical assistance</dd></div>
              <div><dt>Amount</dt><dd>{money(12_000_000)}</dd></div>
              <div><dt>Recipient</dt><dd>hospital-demo-01</dd></div>
              <div><dt>Evidence</dt><dd>Independent review complete</dd></div>
            </dl>
            <div className="state"><span>Status</span><b>{request?.status ?? "NOT CREATED"}</b></div>
          </article>

          <article className="panel allocationPanel">
            <div className="panelHead"><span className="step">02</span><h3>Deterministic match</h3></div>
            {preview ? (
              <>
                <div className="allocationBar">
                  <span style={{ width: "41.67%" }}>A · 5M</span>
                  <span style={{ width: "41.67%" }}>B · 5M</span>
                  <span style={{ width: "16.66%" }}>C · 2M</span>
                </div>
                <ul className="allocations">
                  {preview.allocations.map((item: Json) => (
                    <li key={item.contributionId}><span>{item.contributionId}</span><b>{money(item.amount)}</b></li>
                  ))}
                </ul>
                <p className="total">Matched <b>{money(allocationTotal)}</b></p>
              </>
            ) : <Empty text="Sign in as beneficiary and start the demo to preview eligible sources." />}
            {request?.status === "DRAFT" && (
              <button className="primary full" disabled={busy || !hasRole("beneficiary", "treasurer")} onClick={submit}>Freeze & reserve</button>
            )}
          </article>

          <article className="panel approvalPanel">
            <div className="panelHead"><span className="step">03</span><h3>Digest-bound approvals</h3></div>
            <div className="digest"><span>Canonical SHA-256</span><code>{shortHash(request?.canonicalPayloadHash)}</code></div>
            <div className="approverList">
              {["org-a", "org-b"].map((org, index) => {
                const found = request?.approvals?.find((item: Json) => item.signerOrgId === org);
                return <div key={org}><span className={found ? "approvedDot" : "openDot"} /> <b>Organisation {index ? "B" : "A"}</b><small>{found ? "Approved exact digest" : "Awaiting approval"}</small></div>;
              })}
            </div>
            {request?.status === "PENDING_REVIEW" && (
              <div className="approvalAction">
                <button onClick={approve} disabled={busy || !hasRole("approver") || currentOrgAlreadyApproved}>Approve as signed-in identity</button>
                {!hasRole("approver") && <small>Approver role required. Switch identity above.</small>}
                {hasRole("approver") && currentOrgAlreadyApproved && <small>This organisation has approved. Switch to the other organisation.</small>}
              </div>
            )}
          </article>
        </div>
      </section>

      <section className="security" id="security">
        <div className="sectionHead light">
          <div><p className="eyebrow">Security demo</p><h2>Make the denied path visible</h2></div>
          <p>Every control below names who enforces it. Simulation is never presented as Tide proof.</p>
        </div>
        <div className="securityGrid four">
          <article className="attackCard">
            <p className="cardLabel">Gate 00 · Server RBAC</p>
            <h3>Try an action outside this role.</h3>
            <p>The API resolves roles from its own identity map and returns 403. The browser cannot grant itself a role.</p>
            <button disabled={busy} onClick={testForbiddenAccess}>Verify 403 denial</button>
          </article>
          <article className="attackCard">
            <p className="cardLabel">Attack 01 · Payload tampering</p>
            <h3>Change the recipient after approval.</h3>
            <p>The altered payload produces a different digest, so the existing application approvals no longer match.</p>
            <button disabled={busy || !request?.canonicalPayloadHash || !hasRole("treasurer", "auditor")} onClick={tamper}>Attempt recipient swap</button>
          </article>
          <article className="attackCard">
            <p className="cardLabel">Gate 02 · Approval quorum</p>
            <h3>Require two independent organisations.</h3>
            <p>Checked by the application today. Forseti deployment is still required for Tide-governed signing.</p>
            <button disabled={busy || request?.status !== "READY_TO_AUTHORIZE" || !hasRole("treasurer", "auditor")} onClick={authorize}>Check simulation quorum</button>
          </article>
          <article className="attackCard accent">
            <p className="cardLabel">Gateway 03 · One-time receipt</p>
            <h3>Execute the exact payload once.</h3>
            <p>The isolated gateway recalculates the digest and rejects replay. It does not claim a Tide signature.</p>
            <button disabled={busy || request?.status !== "READY_TO_AUTHORIZE" || !hasRole("treasurer")} onClick={settle}>Simulate settlement</button>
          </article>
        </div>
        {result && (
          <div className={`result ${result.kind}`}>
            <b>{result.kind === "denied" ? "DENIED" : result.kind === "access" ? "API ACCESS DENIED · 403" : result.kind === "receipt" ? "SIMULATION RECEIPT" : "SIMULATION PASSED"}</b>
            <span>{result.reason ?? result.warning ?? result.security?.message}</span>
            {result.receiptId && <code>{result.receiptId}</code>}
          </div>
        )}
      </section>

      <section className="disclosure">
        <p className="eyebrow">Current security posture</p>
        <h2>Designed for TideCloak. Temporarily simulated.</h2>
        <div className="disclosureGrid">
          <div><b>Implemented now</b><p>Server-enforced demo sessions/RBAC, canonical transaction bytes, deterministic matching, atomic reservations, digest-bound app approvals, tamper checks and replay-safe simulation ledger.</p></div>
          <div><b>Prepared, not claimed</b><p>Official Tide Next.js scaffold, DPoP relay, JWT/proof verifier, realm bootstrap and E2EE integration points remain in the repository.</p></div>
          <div><b>Blocked externally</b><p>Real login/E2EE/QEA awaits realm recovery. Transaction signing awaits a custom Forseti contract reviewed and deployed by Tide.</p></div>
        </div>
      </section>

      <footer><span>TrustVault · RMIT Hackathon 2026</span><span>Simulated money only · No banking integration</span></footer>
    </main>
  );
}

function Stat({ label, value, warning = false }: { label: string; value: string; warning?: boolean }) {
  return <div><span>{label}</span><b className={warning ? "warn" : ""}>{value}</b></div>;
}

function Empty({ text }: { text: string }) {
  return <div className="empty"><span>＋</span><p>{text}</p></div>;
}
