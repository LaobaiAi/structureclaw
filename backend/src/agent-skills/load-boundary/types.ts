import type { SkillManifest } from '../../agent-runtime/types.js';

export type LoadBoundarySkillId =
  | 'dead-load'
  | 'live-load'
  | 'wind-load'
  | 'seismic-load'
  | 'temperature-load'
  | 'crane-load'
  | 'load-combination'
  | 'boundary-condition'
  | 'nodal-constraint';

export interface LoadBoundaryExecutionInput {
  skillId: LoadBoundarySkillId;
  action: string;
  params: Record<string, unknown>;
}

export interface LoadBoundaryExecutionOutput {
  status: 'success' | 'error';
  data?: unknown;
  error?: string;
}

export interface LoadBoundarySkillManifest extends SkillManifest {
  domain: 'load-boundary';
  supportedModelFamilies?: string[];
  loadTypes?: string[];
  boundaryTypes?: string[];
  combinationTypes?: string[];
}
