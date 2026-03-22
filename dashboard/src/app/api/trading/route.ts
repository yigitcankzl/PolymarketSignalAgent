import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export async function GET() {
  const filePath = join(process.cwd(), "..", "data", "trader", "latest.json");

  if (!existsSync(filePath)) {
    return NextResponse.json({
      status: "not_configured",
      balance: {},
      positions: [],
      pnl: {},
      orders: [],
    });
  }

  try {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ status: "error", balance: {}, positions: [], pnl: {}, orders: [] }, { status: 500 });
  }
}
