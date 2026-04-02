import { LoadBoundaryRuntimeRunner } from '../agent-skills/load-boundary/entry.js';
import type { LoadBoundaryExecutionInput, LoadBoundaryExecutionOutput } from '../agent-skills/load-boundary/types.js';

export class LoadBoundaryExecutionService {
  constructor(private readonly runner = new LoadBoundaryRuntimeRunner()) {}

  async listSkills(): Promise<{ skills: any[]; defaultSelectionMode: 'auto' }> {
    const { listBuiltinLoadBoundarySkills } = await import('../agent-skills/load-boundary/entry.js');
    const skills = listBuiltinLoadBoundarySkills();
    return { skills, defaultSelectionMode: 'auto' };
  }

  async getSkill(id: string): Promise<any | null> {
    const { getBuiltinLoadBoundarySkill } = await import('../agent-skills/load-boundary/entry.js');
    try {
      return getBuiltinLoadBoundarySkill(id as any) ?? null;
    } catch (error) {
      const statusCode = (error as { statusCode?: number }).statusCode;
      if (statusCode === 404) {
        return null;
      }
      throw error;
    }
  }

  async execute(input: LoadBoundaryExecutionInput): Promise<LoadBoundaryExecutionOutput> {
    return await this.runner.invoke(input);
  }
}
