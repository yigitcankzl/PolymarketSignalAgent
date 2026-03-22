import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

export const dynamic = "force-dynamic";

export async function GET() {
  const filePath = join(process.cwd(), "..", "data", "pipeline_status.json");

  if (!existsSync(filePath)) {
    return NextResponse.json({ running: false, step: 0, total_steps: 7, label: "Idle" });
  }

  try {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ running: false, step: 0, total_steps: 7, label: "Idle" });
  }
}
