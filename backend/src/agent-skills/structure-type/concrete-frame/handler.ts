import { normalizeLegacyDraftPatch } from '../../../agent-runtime/legacy.js';
import type { SkillHandler } from '../../../agent-runtime/types.js';
import { detectConcreteFrameStructuralType } from './detect.js';
import { buildConcreteFrameDraftPatch, coerceConcreteFrameDimension, toConcreteFramePatch } from './extract-llm.js';
import {
  buildConcreteFrameDefaultProposals,
  buildConcreteFrameQuestions,
  buildConcreteFrameReportNarrative,
  computeConcreteFrameMissing,
  mapConcreteFrameLabels,
  resolveConcreteFrameStage,
} from './interaction.js';
import { mergeConcreteFrameState } from './merge.js';
import { buildConcreteFrameModel, getConcreteMaterial, normalizeConcreteGrade, normalizeSectionName } from './model.js';
import type {
  ConcreteBeam,
  ConcreteColumn,
  ConcreteFrameInput,
  ConcreteFrameOutput,
  ConcreteSlab,
} from './types.js';

// ============================================================================
// PR2: 构件生成器
// ============================================================================

/**
 * 生成所有混凝土构件
 * @param input 混凝土框架输入参数
 * @returns 包含梁、柱、板的输出对象
 */
export function generateMembers(input: ConcreteFrameInput): ConcreteFrameOutput {
  const warnings: Array<{ code: string; message: string }> = [];
  const errors: Array<{ code: string; message: string }> = [];

  try {
    const beams = generateBeams(input);
    const columns = generateColumns(input);
    const slabs = generateSlabs(input);

    return { concreteBeams: beams, concreteColumns: columns, concreteSlabs: slabs, warnings, errors };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    errors.push({ code: 'GENERATION_ERROR', message });
    return {
      concreteBeams: [],
      concreteColumns: [],
      concreteSlabs: [],
      warnings,
      errors,
    };
  }
}

/**
 * 生成梁构件
 * 矩形梁: h = span / 10 (主梁) 或 h = span / 14 (次梁)
 * 梁宽 b = h / 2
 * T形梁: 根据 GB/T 50010-2010 表 5.2.4 计算翼缘宽度
 */
export function generateBeams(input: ConcreteFrameInput): ConcreteBeam[] {
  const beams: ConcreteBeam[] = [];
  const { bayWidthsM, beamType = 'rectangular', storyCount } = input;

  // 判断是否为主梁（第一层或截面尺寸较大的为默认主梁）
  const isMainBeam = (index: number) => index === 0 || storyCount <= 3;

  for (let i = 0; i < bayWidthsM.length; i++) {
    const spanM = bayWidthsM[i]!;
    const spanMM = spanM * 1000;
    const isMain = isMainBeam(i);

    // 跨高比：主梁 l/10 ~ l/8，次梁 l/15 ~ l/12
    const spanDepthRatioTarget = isMain ? 10 : 14;
    let heightMM = Math.round((spanMM / spanDepthRatioTarget) / 50) * 50; // 取整到50mm
    heightMM = Math.max(heightMM, 250); // 最小梁高250mm

    // 梁宽 b = h/2，取整到25mm
    let widthMM = Math.round((heightMM / 2) / 25) * 25;
    widthMM = Math.max(widthMM, 200); // 最小梁宽200mm

    if (beamType === 't-shaped') {
      // T形梁计算 (GB/T 50010-2010 表 5.2.4)
      const hf = Math.round(heightMM / 6); // 翼缘厚度取梁高的1/6
      const bw = widthMM; // 腹板宽度等于梁宽
      // 边梁 (首跨或末跨): bf = bw + l0/6; 中梁: bf = bw + l0/3
      // 且 bf ≤ bw + 12*hf
      const isEdge = i === 0 || i === bayWidthsM.length - 1;
      const bfAddend = isEdge ? Math.round(spanMM / 6) : Math.round(spanMM / 3);
      let bf = bw + bfAddend;
      const bfMax = bw + 12 * hf;
      bf = Math.min(bf, bfMax);

      beams.push({
        id: `B-${i + 1}`,
        type: 't-shaped',
        spanM: spanM,
        webWidthMM: bw,
        flangeWidthMM: bf,
        flangeThicknessMM: hf,
        totalHeightMM: heightMM,
        spanDepthRatio: spanMM / heightMM,
        meetsRequirement: (spanMM / heightMM) >= 8 && (spanMM / heightMM) <= 16,
      });
    } else {
      // 矩形梁
      beams.push({
        id: `B-${i + 1}`,
        type: 'rectangular',
        spanM: spanM,
        widthMM: widthMM,
        heightMM: heightMM,
        spanDepthRatio: spanMM / heightMM,
        meetsRequirement: (spanMM / heightMM) >= 8 && (spanMM / heightMM) <= 16,
      });
    }
  }

  // TODO(PR3): 梁配筋计算（正截面、斜截面）
  return beams;
}

/**
 * 生成柱构件
 * 估算公式: N ≤ 0.9 × fc × Ac
 * Ac ≥ N / (0.9 × fc)
 */
export function generateColumns(input: ConcreteFrameInput): ConcreteColumn[] {
  const columns: ConcreteColumn[] = [];
  const {
    storyCount,
    bayCount,
    storyHeightsM,
    bayWidthsM,
    concreteGrade,
    axialLoadKN,
    columnType = 'rectangular',
  } = input;

  // 获取混凝土抗压强度设计值
  const concrete = getConcreteMaterial(concreteGrade);
  const fc = concrete.fc; // N/mm²

  // 轴压比限值 (四级抗震)
  const axialLoadRatioLimit = 0.9;

  // 每层每柱默认轴力(kN)估算：层面积 × 单位荷载 12kN/m²
  const avgSpanM = bayWidthsM.reduce((a, b) => a + b, 0) / bayWidthsM.length;
  const baseLoadKN = axialLoadKN ?? (avgSpanM * storyCount * 120);

  for (let story = 0; story < storyCount; story++) {
    const heightM = storyHeightsM[story] ?? 3.6;

    // 各层轴力从上到下线性递增：底层=baseLoadKN, 顶层=baseLoadKN/storyCount
    const storyN = (baseLoadKN * (story + 1) / storyCount) * 1000; // 转换为 N
    const storyAc = storyN / (axialLoadRatioLimit * fc);

    if (columnType === 'circular') {
      // 圆形柱：d = sqrt(4*Ac/π)，取整到50mm，最小500mm
      // TODO(PR3): 配筋计算与圆形柱正截面验算
      let diameterMM = Math.ceil(Math.sqrt(4 * storyAc / Math.PI) / 50) * 50;
      diameterMM = Math.max(diameterMM, 500);
      const Ac_actual = Math.PI * (diameterMM / 2) ** 2;
      const axialLoadRatio = storyN / (fc * Ac_actual);

      columns.push({
        id: `C-S${story + 1}-1`,
        type: 'circular',
        heightM: heightM,
        diameterMM: diameterMM,
        axialLoadRatio: Math.round(axialLoadRatio * 100) / 100,
        meetsRequirement: axialLoadRatio <= axialLoadRatioLimit,
      });
    } else {
      // 矩形柱截面估算，最小 500mm (GB/T 50010-2010 第 11.4.11 条)
      // TODO(PR3): 矩形柱配筋计算与轴压比精确验算
      const commonSizes = [500, 550, 600, 650, 700, 750, 800, 850, 900];
      let selectedSize = commonSizes[0]!;
      for (const size of commonSizes) {
        if (size * size >= storyAc) {
          selectedSize = size;
          break;
        }
      }
      // 所有预设不够时取计算值
      if (selectedSize === commonSizes[0] && commonSizes[0]! ** 2 < storyAc) {
        selectedSize = Math.ceil(Math.sqrt(storyAc) / 50) * 50;
      }

      // 验算轴压比
      const Ac_actual = selectedSize * selectedSize;
      const axialLoadRatio = storyN / (fc * Ac_actual);

      columns.push({
        id: `C-S${story + 1}-1`,
        type: 'rectangular',
        heightM: heightM,
        widthMM: selectedSize,
        heightMM: selectedSize,
        axialLoadRatio: Math.round(axialLoadRatio * 100) / 100,
        meetsRequirement: axialLoadRatio <= axialLoadRatioLimit,
      });
    }
  }

  return columns;
}

/**
 * 生成板构件
 * 依据: GB/T 50010-2010 第 9.1.2 条
 * 跨厚比限值:
 *   单向板 ≤ 30
 *   双向板 ≤ 40
 *   无梁板（有柱帽） ≤ 35
 *   无梁板（无柱帽） ≤ 30
 *   悬臂板 ≤ 12
 */
export function generateSlabs(input: ConcreteFrameInput): ConcreteSlab[] {
  const slabs: ConcreteSlab[] = [];
  const {
    bayWidthsM,
    slabType = 'one-way',
    slabUsage = 'residential',
  } = input;

  // 跨厚比限值配置
  const spanDepthRatioLimits: Record<string, number> = {
    'one-way': 30,
    'two-way': 40,
    'flat-slab': 30,
    'waffle': 35,
  };

  // 最小厚度配置 (mm) — GB/T 50010-2010 第 9.1.2 条
  // 键: slabType_slabUsage
  const minThicknessMap: Record<string, number> = {
    'one-way_roof': 60,
    'one-way_residential': 60,
    'one-way_commercial': 70,
    'one-way_vehicle': 80,
    'two-way_roof': 100,
    'two-way_residential': 80,
    'two-way_commercial': 80,
    'two-way_vehicle': 80,
    'flat-slab_roof': 150,
    'flat-slab_residential': 150,
    'flat-slab_commercial': 150,
    'flat-slab_vehicle': 150,
    'waffle_roof': 200,
    'waffle_residential': 200,
    'waffle_commercial': 200,
    'waffle_vehicle': 200,
  };

  const spanDepthRatioLimit = spanDepthRatioLimits[slabType] ?? 30;
  const minThicknessKey = `${slabType}_${slabUsage}`;
  const minThickness = minThicknessMap[minThicknessKey] ?? 60;

  for (let i = 0; i < bayWidthsM.length; i++) {
    const spanM = bayWidthsM[i]!;
    const spanMM = spanM * 1000;

    // 计算板厚: t = max(span / 跨厚比, 最小厚度)，向上取整保证跨厚比不超限
    let thicknessMM = Math.ceil((spanMM / spanDepthRatioLimit) / 10) * 10; // 向上取整到10mm
    thicknessMM = Math.max(thicknessMM, minThickness);

    // 验算跨厚比
    const actualSpanDepthRatio = spanMM / thicknessMM;
    const meetsRequirement = actualSpanDepthRatio <= spanDepthRatioLimit;

    slabs.push({
      id: `SL-${i + 1}`,
      type: slabType,
      spanXM: spanM,
      spanYM: spanM, // 假设板为方形区格
      thicknessMM: thicknessMM,
      usage: slabUsage,
      spanDepthRatio: Math.round(actualSpanDepthRatio * 10) / 10,
      meetsRequirement,
    });
  }

  // TODO(PR3): 板配筋计算（板底/板面钢筋）
  return slabs;
}

export const handler: SkillHandler = {
  detectStructuralType(input) {
    return detectConcreteFrameStructuralType(input);
  },

  parseProvidedValues(values) {
    const base = coerceConcreteFrameDimension(
      toConcreteFramePatch(normalizeLegacyDraftPatch(values)),
      undefined,
      JSON.stringify(values),
    );
    return {
      ...base,
      // M1: Separate concrete and rebar grade
      ...(typeof values.frameConcreteGrade === 'string' && { frameConcreteGrade: normalizeConcreteGrade(values.frameConcreteGrade) }),
      ...(typeof values.frameRebarGrade === 'string' && { frameRebarGrade: normalizeConcreteGrade(values.frameRebarGrade) }),
      ...(typeof values.frameColumnSection === 'string' && { frameColumnSection: normalizeSectionName(values.frameColumnSection) }),
      ...(typeof values.frameBeamSection === 'string' && { frameBeamSection: normalizeSectionName(values.frameBeamSection) }),
    };
  },

  extractDraft({ message, llmDraftPatch, currentState }) {
    return buildConcreteFrameDraftPatch(message, llmDraftPatch, currentState);
  },

  mergeState(existing, patch) {
    return mergeConcreteFrameState(existing, patch);
  },

  computeMissing(state, phase) {
    return computeConcreteFrameMissing(state, phase);
  },

  mapLabels(keys, locale) {
    return mapConcreteFrameLabels(keys, locale);
  },

  buildQuestions(keys, criticalMissing, state, locale) {
    return buildConcreteFrameQuestions(keys, criticalMissing, state, locale);
  },

  buildDefaultProposals(keys, state, locale) {
    return buildConcreteFrameDefaultProposals(keys, state, locale);
  },

  buildReportNarrative(input) {
    return buildConcreteFrameReportNarrative(input);
  },

  buildModel(state) {
    try {
      return buildConcreteFrameModel(state);
    } catch (error) {
      console.error('buildConcreteFrameModel failed:', error);
      return undefined;
    }
  },

  resolveStage(missingKeys) {
    return resolveConcreteFrameStage(missingKeys);
  },
};

export default handler;