import { createGatewayServer } from "./app";

const port = Number(process.env.GATEWAY_PORT ?? 3002);
createGatewayServer().listen(port, () => {
  console.log(`TrustVault simulation gateway listening on http://localhost:${port}`);
});
