import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export async function POST(req: Request) {
  const body = await req.json();
  const { token_id, side, amount } = body;

  if (!token_id || !side || !amount) {
    return NextResponse.json({ error: "Missing token_id, side, or amount" }, { status: 400 });
  }

  // Read trader state
  const statePath = join(process.cwd(), "..", "data", "trader", "state.json");
  if (!existsSync(statePath)) {
    return NextResponse.json({ error: "Trading not configured. Run pipeline with --trade first." }, { status: 400 });
  }

  const state = JSON.parse(readFileSync(statePath, "utf-8"));
  if (!state.wallet_id || !state.account_api_key) {
    return NextResponse.json({ error: "Wallet not set up" }, { status: 400 });
  }

  // Place order via Synthesis API
  try {
    const resp = await fetch(
      `https://synthesis.trade/api/v1/wallet/pol/${state.wallet_id}/order`,
      {
        method: "POST",
        headers: {
          "X-API-KEY": state.account_api_key,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token_id,
          side,
          type: "MARKET",
          amount: String(amount),
          units: "USDC",
        }),
      }
    );

    const data = await resp.json();
    return NextResponse.json({
      success: resp.ok,
      order: data,
      status: resp.status,
    });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
