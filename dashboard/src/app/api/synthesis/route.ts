import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export async function GET() {
  const filePath = join(process.cwd(), "..", "data", "synthesis", "latest.json");

  if (!existsSync(filePath)) {
    return NextResponse.json({ markets: [], count: 0 });
  }

  try {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ markets: [], count: 0 }, { status: 500 });
  }
}
