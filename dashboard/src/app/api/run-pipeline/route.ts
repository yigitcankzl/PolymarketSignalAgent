import { NextResponse } from "next/server";
import { exec } from "child_process";
import { join } from "path";

export async function POST() {
  const projectRoot = join(process.cwd(), "..");
  const venvPython = join(projectRoot, "venv", "bin", "python3");
  const systemPython = "python3";

  // Try venv first, fallback to system python
  const python = await new Promise<string>((resolve) => {
    exec(`${venvPython} --version`, (err) => {
      resolve(err ? systemPython : venvPython);
    });
  });

  const cmd = `cd "${projectRoot}" && ${python} -m engine.main --markets 10 2>&1`;

  return new Promise<Response>((resolve) => {
    exec(cmd, { timeout: 180000, maxBuffer: 1024 * 1024 * 5 }, (error, stdout, stderr) => {
      const output = stdout || stderr || "";
      const signalMatch = output.match(/(\d+) actionable/);
      const arbMatch = output.match(/Found (\d+) arbitrage/);

      resolve(NextResponse.json({
        success: !error,
        signals: signalMatch ? parseInt(signalMatch[1]) : 0,
        arbitrage: arbMatch ? parseInt(arbMatch[1]) : 0,
        output: output.slice(-500),
      }));
    });
  });
}
