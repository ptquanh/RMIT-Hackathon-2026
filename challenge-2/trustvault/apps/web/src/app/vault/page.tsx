export default function VaultStatusPage() {
  return (
    <main className="simplePage">
      <p className="eyebrow">Tide E2EE status</p>
      <h1>Evidence vault pending realm recovery</h1>
      <p>
        The official Tide E2EE scaffold and server-side JWT/DPoP verification helpers are preserved in this repository.
        The beneficiary evidence flow stays disabled until encryption and a denied decryption are verified against a real realm.
      </p>
      <a className="secondary" href="/">Return to TrustVault</a>
    </main>
  );
}
