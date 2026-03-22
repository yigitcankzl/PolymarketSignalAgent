import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export async function GET() {
  const filePath = join(process.cwd(), "..", "data", "backtest", "latest.json");

  if (!existsSync(filePath)) {
    return NextResponse.json({ metrics: null, pnl_curve: [], trades: [] });
  }

  try {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ metrics: null, pnl_curve: [], trades: [] }, { status: 500 });
  }
}
