import type { LoadBoundarySkillManifest } from './types.js';
import type { LoadBoundarySkillId } from './types.js';

// Load boundary skill manifests
export const BUILTIN_LOAD_BOUNDARY_SKILLS: LoadBoundarySkillManifest[] = [
  {
    id: 'dead-load',
    name: { en: 'Dead Load', zh: '恒荷载' },
    description: {
      en: 'Generate dead loads for structural analysis including gravity loads from structural elements and fixed equipment',
      zh: '生成恒荷载，包括结构构件自重和固定设备重力荷载'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 100,
    stages: ['analysis'],
    capabilities: ['load-generation', 'load-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    loadTypes: ['dead', 'fixed', 'self-weight'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['dead load', '恒载', 'self weight', '自重', 'fixed load', '固定荷载'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        density: { type: 'number' },
        includeSelfWeight: { type: 'boolean' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        loadCases: { type: 'array' },
        loads: { type: 'array' },
      },
    },
  },
  {
    id: 'live-load',
    name: { en: 'Live Load', zh: '活荷载' },
    description: {
      en: 'Generate live loads including floor loads, roof loads, and other variable loads according to GB50009-2012',
      zh: '生成活荷载，包括楼面荷载、屋面荷载及其他可变荷载，符合GB50009-2012规范'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 95,
    stages: ['analysis'],
    capabilities: ['load-generation', 'load-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    loadTypes: ['live', 'floor', 'roof'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['live load', '活载', 'floor load', '楼面荷载', 'roof load', '屋面荷载', 'variable load', '可变荷载'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        floorArea: { type: 'number' },
        loadCategory: { type: 'string' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        loadCases: { type: 'array' },
        loads: { type: 'array' },
      },
    },
  },
  {
    id: 'wind-load',
    name: { en: 'Wind Load', zh: '风荷载' },
    description: {
      en: 'Generate wind loads according to GB50009-2012 including exposure categories and building shapes',
      zh: '生成风荷载，符合GB50009-2012规范，包括暴露类别和建筑形状'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 90,
    stages: ['analysis'],
    capabilities: ['load-generation', 'load-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    loadTypes: ['wind', 'static', 'dynamic'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['wind load', '风载', 'wind pressure', '风压', 'wind force', '风力'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        windZone: { type: 'string' },
        buildingHeight: { type: 'number' },
        exposureCategory: { type: 'string' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        loadCases: { type: 'array' },
        loads: { type: 'array' },
      },
    },
  },
  {
    id: 'seismic-load',
    name: { en: 'Seismic Load', zh: '地震荷载' },
    description: {
      en: 'Generate seismic loads using equivalent base shear method according to GB50011-2010 with multiple force distribution strategies',
      zh: '生成地震荷载，使用底部剪力法，符合GB50011-2010规范，支持多种力分配策略'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 95,
    stages: ['analysis'],
    capabilities: ['load-generation', 'load-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    loadTypes: ['seismic', 'earthquake', 'dynamic'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['seismic load', '地震荷载', 'earthquake load', '地震力', 'seismic analysis', '抗震'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        seismicIntensity: { type: 'string' },
        siteClass: { type: 'string' },
        designGroup: { type: 'string' },
        dampingRatio: { type: 'number' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        loadCases: { type: 'array' },
        loads: { type: 'array' },
      },
    },
  },
  {
    id: 'temperature-load',
    name: { en: 'Temperature Load', zh: '温度荷载' },
    description: {
      en: 'Generate temperature loads for thermal expansion and contraction effects',
      zh: '生成温度荷载，考虑热胀冷缩效应'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 85,
    stages: ['analysis'],
    capabilities: ['load-generation'],
    supportedModelFamilies: ['frame', 'truss'],
    loadTypes: ['temperature', 'thermal'],
    autoLoadByDefault: false,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['temperature load', '温度荷载', 'thermal load', '热荷载', 'thermal expansion', '热胀冷缩'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        temperatureChange: { type: 'number' },
        expansionCoefficient: { type: 'number' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        loadCases: { type: 'array' },
        loads: { type: 'array' },
      },
    },
  },
  {
    id: 'crane-load',
    name: { en: 'Crane Load', zh: '吊车荷载' },
    description: {
      en: 'Generate crane loads for industrial buildings with multiple crane configurations',
      zh: '生成吊车荷载，适用于工业建筑，支持多种吊车配置'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 90,
    stages: ['analysis'],
    capabilities: ['load-generation', 'load-validation'],
    supportedModelFamilies: ['frame', 'generic'],
    loadTypes: ['crane', 'vertical', 'horizontal'],
    autoLoadByDefault: false,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['crane load', '吊车荷载', 'bridge crane', '桥式起重机', 'overhead crane', '行车'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        craneCapacity: { type: 'number' },
        craneSpan: { type: 'number' },
        numberOfCranes: { type: 'number' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        loadCases: { type: 'array' },
        loads: { type: 'array' },
      },
    },
  },
  {
    id: 'load-combination',
    name: { en: 'Load Combination', zh: '荷载组合' },
    description: {
      en: 'Generate load combinations for ultimate and serviceability limit states including seismic combinations',
      zh: '生成荷载组合，包括承载力极限状态和正常使用极限状态组合，以及地震组合'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 100,
    stages: ['analysis'],
    capabilities: ['load-combination', 'load-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    combinationTypes: ['ULS', 'SLS', 'SEISMIC'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['load combination', '荷载组合', 'ULS', 'SLS', 'ultimate limit state', '承载力极限状态', 'serviceability limit state', '正常使用极限状态'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        loadCases: { type: 'array' },
        combinationType: { type: 'string' },
        code: { type: 'string' },
      },
      required: ['modelId', 'loadCases'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        combinations: { type: 'array' },
      },
    },
  },
  {
    id: 'boundary-condition',
    name: { en: 'Boundary Condition', zh: '边界条件' },
    description: {
      en: 'Define boundary conditions including nodal constraints and member end releases',
      zh: '定义边界条件，包括节点约束和杆端释放'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 95,
    stages: ['analysis'],
    capabilities: ['boundary-definition', 'constraint-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    boundaryTypes: ['fixed', 'pinned', 'roller', 'elastic'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['boundary condition', '边界条件', 'constraint', '约束', 'support', '支座', 'fixed support', '固定支座', 'pinned support', '铰支座'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        constraints: { type: 'array' },
        endReleases: { type: 'array' },
      },
      required: ['modelId'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        constraints: { type: 'array' },
        updatedModel: { type: 'object' },
      },
    },
  },
  {
    id: 'nodal-constraint',
    name: { en: 'Nodal Constraint', zh: '节点约束' },
    description: {
      en: 'Define nodal constraints including restraints and elastic supports',
      zh: '定义节点约束，包括刚性约束和弹性支座'
    },
    domain: 'load-boundary',
    version: '1.0.0',
    priority: 90,
    stages: ['analysis'],
    capabilities: ['boundary-definition', 'constraint-validation'],
    supportedModelFamilies: ['frame', 'truss', 'generic'],
    boundaryTypes: ['fixed', 'pinned', 'roller', 'elastic', 'guided'],
    autoLoadByDefault: true,
    scenarioKeys: ['frame', 'truss', 'portal-frame', 'double-span-beam', 'beam'],
    triggers: ['nodal constraint', '节点约束', 'node support', '节点支座', 'restraint', '约束', 'elastic support', '弹性支座'],
    requires: [],
    conflicts: [],
    compatibility: {
      minRuntimeVersion: '1.0.0',
      skillApiVersion: '1.0.0',
    },
    inputSchema: {
      type: 'object',
      properties: {
        modelId: { type: 'string' },
        nodeId: { type: 'string' },
        constraintType: { type: 'string' },
        stiffness: { type: 'object' },
      },
      required: ['modelId', 'nodeId', 'constraintType'],
    },
    outputSchema: {
      type: 'object',
      properties: {
        node: { type: 'object' },
      },
    },
  },
];

export function getBuiltinLoadBoundarySkill(id: LoadBoundarySkillId): LoadBoundarySkillManifest | undefined {
  return BUILTIN_LOAD_BOUNDARY_SKILLS.find((skill) => skill.id === id);
}

export function listBuiltinLoadBoundarySkills(): LoadBoundarySkillManifest[] {
  return [...BUILTIN_LOAD_BOUNDARY_SKILLS];
}

export function listLoadBoundarySkillsByCapability(capability: string): LoadBoundarySkillManifest[] {
  return BUILTIN_LOAD_BOUNDARY_SKILLS.filter((skill) =>
    skill.capabilities.includes(capability)
  );
}
