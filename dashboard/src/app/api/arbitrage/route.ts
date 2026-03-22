import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export async function GET() {
  const filePath = join(process.cwd(), "..", "data", "arbitrage", "latest.json");

  if (!existsSync(filePath)) {
    return NextResponse.json({ intra_market: [], related_market: [], total_opportunities: 0 });
  }

  try {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ intra_market: [], related_market: [], total_opportunities: 0 }, { status: 500 });
  }
}
