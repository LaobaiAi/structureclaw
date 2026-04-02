import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { LoadBoundaryExecutionInput, LoadBoundaryExecutionOutput } from './types.js';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class LoadBoundaryRuntimeRunner {
  private readonly pythonPath: string;
  private readonly skillBasePath: string;

  constructor(options?: { pythonPath?: string; skillBasePath?: string }) {
    this.pythonPath = options?.pythonPath ?? 'python';
    this.skillBasePath = options?.skillBasePath ?? __dirname;
  }

  async invoke(input: LoadBoundaryExecutionInput): Promise<LoadBoundaryExecutionOutput> {
    const { skillId, action, params } = input;

    const skillPath = path.join(this.skillBasePath, skillId);
    const runtimePath = path.join(skillPath, 'runtime.py');

    // Prepare Python script execution
    const script = `
import sys
sys.path.insert(0, '${this.skillBasePath.replace(/\\/g, '\\\\')}')

try:
    import json
    from ${skillId.replace(/-/g, '_')}.runtime import execute

    params = json.loads('${JSON.stringify(params).replace(/'/g, "\\'").replace(/\\/g, '\\\\')}')

    result = execute(params)

    print(json.dumps({
        'status': 'success',
        'data': result
    }, ensure_ascii=False))
except Exception as e:
    import traceback
    print(json.dumps({
        'status': 'error',
        'error': str(e),
        'traceback': traceback.format_exc()
    }, ensure_ascii=False))
`;

    try {
      const { stdout, stderr } = await execAsync(
        `"${this.pythonPath}" -c "${script.replace(/"/g, '\\"')}"`,
        {
          cwd: this.skillBasePath,
          timeout: 30000,
        }
      );

      if (stderr && stderr.length > 0) {
        console.warn(`LoadBoundary runtime warning: ${stderr}`);
      }

      const output = JSON.parse(stdout.trim());
      if (output.status === 'error') {
        throw new Error(output.error || 'Unknown error');
      }

      return {
        status: 'success',
        data: output.data,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`LoadBoundary runtime execution failed: ${errorMessage}`);
    }
  }
}
