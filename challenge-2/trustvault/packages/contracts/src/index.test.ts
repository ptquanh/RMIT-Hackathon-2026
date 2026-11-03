import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { canonicalize, sha256Canonical } from "./index";

describe("canonical transaction serializer", () => {
  it("sorts object keys recursively while preserving array order", () => {
    assert.equal(canonicalize({ z: 1, a: { y: 2, b: 3 }, list: [{ d: 4, c: 5 }] }),
      '{"a":{"b":3,"y":2},"list":[{"c":5,"d":4}],"z":1}',
    );
  });

  it("produces a different digest when the recipient changes", () => {
    const original = { amount: "12000000", recipientRef: "hospital-demo-01" };
    const tampered = { ...original, recipientRef: "attacker-wallet" };
    assert.notEqual(sha256Canonical(original), sha256Canonical(tampered));
  });
});
