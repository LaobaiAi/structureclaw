import type { AppLocale } from '../services/locale.js';

export type DraftLoadType = 'point' | 'distributed';
export type DraftLoadPosition = 'end' | 'midspan' | 'full-span' | 'top-nodes' | 'middle-joint' | 'free-joint';
export type DraftSupportType = 'cantilever' | 'simply-supported' | 'fixed-fixed' | 'fixed-pinned';
export type FrameDimension = '2d' | '3d';
export type FrameBaseSupportType = 'fixed' | 'pinned';
export type AgentAnalysisType = 'static' | 'dynamic' | 'seismic' | 'nonlinear';
export type MaterialFamily = 'steel' | 'concrete' | 'composite' | 'timber' | 'masonry' | 'generic';

export interface DraftFloorLoad {
  story: number;
  verticalKN?: number;
  lateralXKN?: number;
  lateralYKN?: number;
}

// ============================================================================
// 荷载工况接口 - 与 V2 Schema (structure_model_v2.py LoadCaseV2) 对齐
// ============================================================================

export interface LoadCase {
  id: string;                    // 荷载工况ID (对齐 V2 Schema)
  type: LoadCaseTypeEnum;         // 荷载类型 (对齐 V2 Schema)
  loads?: LoadAction[];           // 荷载动作列表 (对齐 V2 Schema)
  description?: string;           // 描述 (对齐 V2 Schema)
  extra?: Record<string, any>;    // 扩展字段 (对齐 V2 Schema)
}

// ============================================================================
// 荷载动作接口 - V2 Schema 使用 Dict[str, Any]，此处定义具体结构
// ============================================================================

export interface LoadAction {
  id?: string;                    // 动作ID (可选，V2 Schema 允许任意字段)
  caseId?: string;                // 所属工况ID (可选，V2 Schema 允许任意字段)
  elementType?: LoadElementTypeEnum; // 单元类型 (可选，V2 Schema 允许任意字段)
  elementId?: string;             // 单元ID (可选，V2 Schema 允许任意字段)
  loadType?: LoadTypeEnum;        // 荷载类型 (可选，V2 Schema 允许任意字段)
  loadValue?: number;             // 荷载值 (可选，V2 Schema 允许任意字段)
  loadDirection?: Vector3D;       // 荷载方向向量 (可选，V2 Schema 允许任意字段)
  position?: Vector3D;            // 作用位置 (可选，V2 Schema 允许任意字段)
  extra?: Record<string, any>;     // 扩展字段 (对齐 V2 Schema)
}

// ============================================================================
// 节点约束接口 - V2 Schema 使用 restraints: List[bool]，此处提供扩展定义
// ============================================================================

export interface NodalConstraint {
  nodeId: string;                // 节点ID
  constraintType?: NodalConstraintTypeEnum; // 约束类型 (可选，V2 Schema 未定义)
  restraints?: [boolean, boolean, boolean, boolean, boolean, boolean]; // 对齐 V2 Schema: [ux, uy, uz, rx, ry, rz]
  restrainedDOFs?: DOFSet;       // 约束的自由度 (可选，与 V2 Schema 格式不同)
  stiffness?: Matrix6x6;         // 弹簧刚度矩阵 (可选，V2 Schema 允许任意字段)
  extra?: Record<string, any>;    // 扩展字段 (对齐 V2 Schema)
}

// ============================================================================
// 杆端释放接口 - V2 Schema 使用 releases: Dict[str, Any]，此处提供扩展定义
// ============================================================================

export interface MemberEndRelease {
  memberId: string;              // 杆件ID
  releaseI?: DOFSet;             // I端释放 (可选，V2 Schema 允许任意字段)
  releaseJ?: DOFSet;             // J端释放 (可选，V2 Schema 允许任意字段)
  springStiffnessI?: Vector6D;   // I端弹簧刚度 (可选，V2 Schema 允许任意字段)
  springStiffnessJ?: Vector6D;   // J端弹簧刚度 (可选，V2 Schema 允许任意字段)
  extra?: Record<string, any>;    // 扩展字段 (对齐 V2 Schema)
}

// ============================================================================
// 计算长度接口 - V2 Schema 未定义，此处提供扩展定义
// ============================================================================

export interface EffectiveLength {
  memberId: string;              // 杆件ID
  direction?: AxisDirectionEnum; // 方向 (可选)
  calcLength?: number;           // 几何长度 (可选)
  lengthFactor?: number;         // 长度系数 (可选)
  effectiveLength?: number;      // 计算长度 (可选)
  extra?: Record<string, any>;    // 扩展字段 (对齐 V2 Schema)
}

// ============================================================================
// 荷载与边界条件相关类型定义
// 对齐 V2 Schema (structure_model_v2.py)
// 对应 #48 Issue：feat(skills): define load and boundary condition skills
// ============================================================================

// 荷载工况类型枚举 - 完全对齐 V2 Schema LoadCaseV2.type
export enum LoadCaseTypeEnum {
  DEAD = 'dead',              // 恒载 (对齐 V2 Schema)
  LIVE = 'live',              // 活载 (对齐 V2 Schema)
  WIND = 'wind',              // 风载 (对齐 V2 Schema)
  SEISMIC = 'seismic',        // 地震 (对齐 V2 Schema)
  TEMPERATURE = 'temperature', // 温度 (对齐 V2 Schema)
  SETTLEMENT = 'settlement',  // 沉降 (对齐 V2 Schema)
  CRANE = 'crane',            // 吊车 (对齐 V2 Schema)
  SNOW = 'snow',              // 雪 (对齐 V2 Schema)
  OTHER = 'other',            // 其他 (对齐 V2 Schema)
}

// 荷载动作类型枚举
export enum LoadTypeEnum {
  POINT_FORCE = 'point_force',         // 集中力
  DISTRIBUTED_LOAD = 'distributed_load', // 均布荷载
  MOMENT = 'moment',                 // 弯矩
  TORQUE = 'torque',               // 扭矩
  AXIAL_FORCE = 'axial_force',     // 轴向力
}

// 作用元素类型枚举
export enum LoadElementTypeEnum {
  NODE = 'node',
  BEAM = 'beam',
  COLUMN = 'column',
  WALL = 'wall',
  SLAB = 'slab'
}

// 节点约束类型枚举
export enum NodalConstraintTypeEnum {
  FIXED = 'fixed',           // 固定支座
  PINNED = 'pinned',       // 铰支座
  SLIDING = 'sliding',      // 滑动支座
  ELASTIC = 'elastic',        // 弹性支座（预留，待 #39 Schema 确认）
}

// 自由度集合类型
export interface DOFSet {
  uX: boolean;  // X 轴平动位移
  uY: boolean;  // Y 轴平动位移
  uZ: boolean;  // Z 轴平动位移
  rotX: boolean;  // X 轴转角位移
  rotY: boolean;  // Y 轴转角位移
  rotZ: boolean;  // Z 轴转角位移
}

// V2 Schema 格式的 DOF 约束 - 对齐 NodeV2.restraints: List[bool]
export type RestraintDOF = [boolean, boolean, boolean, boolean, boolean, boolean];
// 格式: [ux, uy, uz, rx, ry, rz]
// True = 约束, False = 自由

// 弹性刚度矩阵（6x6）
export interface Matrix6x6 {
  xx: number;  // 弯曲刚度
  xy: number;  // XY 剪切刚度
  xz: number;  // XZ 扭剪刚度
  yx: number;  // YX 扭剪刚度
  yy: number;  // YY 扭剪刚度
  yz: number;  // YZ 扭剪刚度
  zx: number;  // ZX 扭剪刚度
  zy: number;  // ZY 扭剪刚度
}

// 三维向量
export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

// 六维向量
export interface Vector6D {
  xx: number;  // 弯曲分量
  xy: number;  // 剪切分量
  xz: number;  // 扭剪分量
  yx: number;  // 扭剪分量
  yy: number;  // 扭剪分量
  yz: number;  // 扭剪分量
  zx: number;  // 扭剪分量
  zy: number;  // 扭剪刚度
}

// 方向枚举（用于计算长度）
export enum AxisDirectionEnum {
  STRONG_AXIS = 'strong_axis',    // 强轴
  WEAK_AXIS = 'weak_axis',      // 弱轴
  INCLINED_AXIS = 'inclined_axis' // 斜轴
}

export type InferredModelType = 'beam' | 'truss' | 'portal-frame' | 'double-span-beam' | 'frame' | 'unknown';
export type ScenarioTemplateKey =
  | 'beam'
  | 'truss'
  | 'portal-frame'
  | 'double-span-beam'
  | 'frame'
  | 'steel-frame'
  | 'portal'
  | 'girder'
  | 'space-frame'
  | 'plate-slab'
  | 'shell'
  | 'tower'
  | 'bridge'
  | 'unknown';
export type ScenarioSupportLevel = 'supported' | 'fallback' | 'unsupported';
export type SkillStage = 'intent' | 'draft' | 'analysis' | 'design';

export interface ScenarioMatch {
  key: ScenarioTemplateKey;
  mappedType: InferredModelType;
  skillId?: string;
  supportLevel: ScenarioSupportLevel;
  supportNote?: string;
}

export interface DraftState {
  inferredType: InferredModelType;
  skillId?: string;
  scenarioKey?: ScenarioTemplateKey;
  supportLevel?: ScenarioSupportLevel;
  supportNote?: string;
  skillState?: Record<string, unknown>;
  lengthM?: number;
  spanLengthM?: number;
  heightM?: number;
  supportType?: DraftSupportType;
  frameDimension?: FrameDimension;
  storyCount?: number;
  bayCount?: number;
  bayCountX?: number;
  bayCountY?: number;
  storyHeightsM?: number[];
  bayWidthsM?: number[];
  bayWidthsXM?: number[];
  bayWidthsYM?: number[];
  floorLoads?: DraftFloorLoad[];
  frameBaseSupportType?: FrameBaseSupportType;
  loadKN?: number;
  loadType?: DraftLoadType;
  loadPosition?: DraftLoadPosition;
  loadPositionM?: number;
  updatedAt: number;
  [key: string]: unknown;
}

export interface DraftExtraction {
  inferredType?: InferredModelType;
  skillId?: string;
  scenarioKey?: ScenarioTemplateKey;
  supportLevel?: ScenarioSupportLevel;
  supportNote?: string;
  skillState?: Record<string, unknown>;
  lengthM?: number;
  spanLengthM?: number;
  heightM?: number;
  supportType?: DraftSupportType;
  frameDimension?: FrameDimension;
  storyCount?: number;
  bayCount?: number;
  bayCountX?: number;
  bayCountY?: number;
  storyHeightsM?: number[];
  bayWidthsM?: number[];
  bayWidthsXM?: number[];
  bayWidthsYM?: number[];
  floorLoads?: DraftFloorLoad[];
  frameBaseSupportType?: FrameBaseSupportType;
  loadKN?: number;
  loadType?: DraftLoadType;
  loadPosition?: DraftLoadPosition;
  loadPositionM?: number;
  [key: string]: unknown;
}

export interface DraftResult {
  inferredType: InferredModelType;
  missingFields: string[];
  model?: Record<string, unknown>;
  extractionMode: 'llm' | 'rule-based';
  stateToPersist?: DraftState;
  scenario?: ScenarioMatch;
}

export interface InteractionQuestion {
  paramKey: string;
  label: string;
  question: string;
  unit?: string;
  required: boolean;
  critical: boolean;
  suggestedValue?: unknown;
}

export interface LocalizedText {
  zh: string;
  en: string;
}

export interface AgentSkillMetadata {
  id: string;
  structureType: Exclude<InferredModelType, 'unknown'>;
  name: LocalizedText;
  description: LocalizedText;
  triggers: string[];
  stages: SkillStage[];
  autoLoadByDefault: boolean;
}

export interface AgentSkillFile extends AgentSkillMetadata {
  stage: SkillStage;
  markdown: string;
}

export interface AgentSkillBundle extends AgentSkillMetadata {
  markdownByStage: Partial<Record<SkillStage, string>>;
}

export type SkillDomain =
  | 'structure-type'
  | 'material-constitutive'
  | 'geometry-input'
  | 'load-boundary'
  | 'analysis-strategy'
  | 'code-check'
  | 'result-postprocess'
  | 'visualization'
  | 'report-export'
  | 'generic-fallback';

export interface SkillCompatibility {
  minRuntimeVersion: string;
  skillApiVersion: string;
}

export interface SkillManifest extends AgentSkillMetadata {
  scenarioKeys: ScenarioTemplateKey[];
  domain: SkillDomain;
  requires: string[];
  conflicts: string[];
  capabilities: string[];
  supportedAnalysisTypes?: AgentAnalysisType[];
  materialFamilies?: MaterialFamily[];
  priority: number;
  compatibility: SkillCompatibility;
}

export interface SkillDetectionInput {
  message: string;
  locale: AppLocale;
  currentState?: DraftState;
}

export interface SkillDraftContext {
  message: string;
  locale: AppLocale;
  currentState?: DraftState;
  llmDraftPatch?: Record<string, unknown> | null;
  scenario: ScenarioMatch;
}

export interface SkillMissingResult {
  critical: string[];
  optional: string[];
}

export interface SkillDefaultProposal {
  paramKey: string;
  value: unknown;
  reason: string;
}

export interface SkillReportNarrativeInput {
  message: string;
  analysisType: AgentAnalysisType;
  analysisSuccess: boolean;
  codeCheckText: string;
  summary: string;
  keyMetrics: Record<string, unknown>;
  clauseTraceability: Array<Record<string, unknown>>;
  controllingCases: Record<string, unknown>;
  visualizationHints: Record<string, unknown>;
  locale: AppLocale;
}

export interface SkillHandler {
  detectScenario(input: SkillDetectionInput): ScenarioMatch | null;
  parseProvidedValues(values: Record<string, unknown>): DraftExtraction;
  extractDraft(input: SkillDraftContext): DraftExtraction;
  mergeState(existing: DraftState | undefined, patch: DraftExtraction): DraftState;
  computeMissing(state: DraftState, mode: 'chat' | 'execute'): SkillMissingResult;
  mapLabels(keys: string[], locale: AppLocale): string[];
  buildQuestions(keys: string[], criticalMissing: string[], state: DraftState, locale: AppLocale): InteractionQuestion[];
  buildDefaultProposals?(keys: string[], state: DraftState, locale: AppLocale): SkillDefaultProposal[];
  buildReportNarrative?(input: SkillReportNarrativeInput): string;
  buildModel(state: DraftState): Record<string, unknown> | undefined;
  resolveStage?(missingKeys: string[], state: DraftState): 'intent' | 'model' | 'loads' | 'analysis' | 'code_check' | 'report';
}

export interface AgentSkillPlugin extends AgentSkillBundle {
  manifest: SkillManifest;
  handler: SkillHandler;
}

export interface SkillExecutionResult {
  detectedScenario?: ScenarioTemplateKey;
  inferredType?: InferredModelType;
  draftPatch?: DraftExtraction;
  missingCritical?: string[];
  missingOptional?: string[];
  questions?: InteractionQuestion[];
  defaultProposals?: Array<{ paramKey: string; value: unknown; reason: string }>;
  stage?: 'intent' | 'model' | 'loads' | 'analysis' | 'code_check' | 'report';
  supportLevel?: ScenarioSupportLevel;
  supportNote?: string;
}

export interface AgentSkillExecutorInput {
  message: string;
  locale: AppLocale;
  existingState?: DraftState;
  selectedSkill: AgentSkillPlugin;
}
