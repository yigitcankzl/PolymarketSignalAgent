import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export async function GET() {
  const filePath = join(process.cwd(), "..", "data", "signals", "latest.json");

  if (!existsSync(filePath)) {
    return NextResponse.json({ signals: [], total_signals: 0, actionable_signals: 0 });
  }

  try {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ signals: [], total_signals: 0, actionable_signals: 0 }, { status: 500 });
  }
}
