"use client";

/**
 * Temporary organiser-approved simulation shell.
 *
 * The official Tide scaffold, DPoP asset, verifier, and bootstrap scripts remain in this app.
 * Once the partially-created realm is recovered, this wrapper must be replaced by the original
 * TideCloakProvider using the exported adapter JSON. Until then, no UI state is represented as
 * Tide-authenticated.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return children;
}
