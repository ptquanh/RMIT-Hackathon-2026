import { Providers } from "./providers";
import "./globals.css";

export const metadata = {
  title: "TrustVault — purpose-bound funding",
  description: "Conditional cross-organisation funding without unilateral override",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
