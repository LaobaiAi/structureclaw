import type {
  LocalizedText,
  SkillDomain,
  SkillStage,
  SkillCompatibility,
  AgentAnalysisType,
  MaterialFamily,
} from '../../agent-runtime/types.js';
import type { ScenarioTemplateKey } from '../../agent-runtime/types.js';

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

export interface LoadBoundarySkillManifest {
  id: string;
  structureType?: string; // Optional for cross-domain skills
  name: LocalizedText;
  description: LocalizedText;
  triggers?: string[]; // Optional for cross-domain skills
  stages: SkillStage[];
  autoLoadByDefault: boolean;
  scenarioKeys: ScenarioTemplateKey[];
  domain: 'load-boundary';
  version: string;
  requires: string[];
  conflicts: string[];
  capabilities: string[];
  supportedAnalysisTypes?: AgentAnalysisType[];
  materialFamilies?: MaterialFamily[];
  priority: number;
  compatibility: SkillCompatibility;
  supportedModelFamilies?: string[];
  loadTypes?: string[];
  boundaryTypes?: string[];
  combinationTypes?: string[];
  inputSchema?: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
}
