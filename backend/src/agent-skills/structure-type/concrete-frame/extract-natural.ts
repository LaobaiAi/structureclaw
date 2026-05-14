import { normalizeNumber } from '../../../agent-runtime/fallback.js';
import type { DraftExtraction, DraftState } from '../../../agent-runtime/types.js';

// Pattern to match both Arabic and Chinese digits: 0-9 or 零一二三四五六七八九十
const DIGIT_PATTERN = '[零一二三四五六七八九十0-9]+';

function _extractNaturalScalar(message: string, patterns: RegExp[]): number | undefined {
  for (const pattern of patterns) {
    const match = message.match(pattern);
    if (match?.[1]) return normalizeNumber(match[1]);
  }
  return undefined;
}

function _extractNaturalCount(message: string, patterns: RegExp[]): number | undefined {
  for (const pattern of patterns) {
    const match = message.match(pattern);
    if (match?.[1]) return normalizeNumber(match[1]);
  }
  return undefined;
}

function _extractNaturalArray(message: string, patterns: RegExp[]): number[] | undefined {
  for (const pattern of patterns) {
    const matches = message.matchAll(pattern);
    const values: number[] = [];
    for (const match of matches) {
      const value = normalizeNumber(match[1]);
      if (value !== undefined && value > 0) values.push(value);
    }
    if (values.length > 0) return values;
  }
  return undefined;
}

function extractStoryCount(message: string): number | undefined {
  return _extractNaturalCount(message, [
    new RegExp(`(?:层数|楼层|story\\s*count|story\\s*number|stories?)\\s*[：:]*\\s*(${DIGIT_PATTERN})`, 'i'),
    new RegExp(`(?:共|有|总共|总计)\\s*(${DIGIT_PATTERN})\\s*(?:层|楼|stories?)`, 'i'),
    new RegExp(`(${DIGIT_PATTERN})\\s*(?:层|楼|stories?)`, 'i'),
  ]);
}

function extractStoryHeights(message: string): number[] | undefined {
  return _extractNaturalArray(message, [
    new RegExp(`(?:层高|story\\s*height)\\s*[：:]*\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)`, 'gi'),
    // English: "4.2m each" - number and unit before "each" or "per story"
    new RegExp(`(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m\\s*(?:each|per\\s*story|per\\s*floor)(?=\\s|,|$)`, 'gi'),
    // Chinese: "每层3m" or "每层 3m" - "每层" followed by optional space and number
    new RegExp(`每层\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m(?=\\s|,|$)`, 'gi'),
  ]);
}

// Extract direction-specific bay count from patterns like "x方向4跨"
function extractBayCountX(message: string): number | undefined {
  return _extractNaturalCount(message, [
    // x方向 followed by number and 跨
    new RegExp(`x方向\\s*(${DIGIT_PATTERN})\\s*跨`, 'i'),
    // 方向前有x (e.g., "向x 4跨" or "x向4跨")
    new RegExp(`x?向\\s*${DIGIT_PATTERN}\\s*跨|${DIGIT_PATTERN}\\s*跨\\s*(?:间距|间隔)`, 'i'),
  ]);
}

// Extract direction-specific bay count from patterns like "y方向3跨"
function extractBayCountY(message: string): number | undefined {
  return _extractNaturalCount(message, [
    new RegExp(`y方向\\s*(${DIGIT_PATTERN})\\s*跨`, 'i'),
    new RegExp(`y向\\s*(${DIGIT_PATTERN})\\s*跨`, 'i'),
  ]);
}

function extractBayCount(message: string): number | undefined {
  // First check for explicit "single bay" or "one bay" patterns
  if (/\bsingle\s*bay\b/i.test(message) || /\bone\s*bay\b/i.test(message)) {
    return 1;
  }
  if (/\bdouble\s*bay\b/i.test(message) || /\btwo\s*bays?\b/i.test(message)) {
    return 2;
  }
  if (/\bthree\s*bays?\b/i.test(message)) {
    return 3;
  }
  return _extractNaturalCount(message, [
    new RegExp(`(?:跨数|bay\\s*count|span\\s*count)\\s*[：:]*\\s*(${DIGIT_PATTERN})`, 'i'),
    new RegExp(`(?:共|有|总共|总计)\\s*(${DIGIT_PATTERN})\\s*(?:跨|bays?)`, 'i'),
  ]);
}

// Extract bay widths for x-direction (in context of x方向)
function extractBayWidthsX(message: string): number[] | undefined {
  // Check if message has x-direction context
  if (!/x方向|x向/i.test(message)) {
    return undefined;
  }
  return _extractNaturalArray(message, [
    // "间隔3m" after x方向 context
    new RegExp(`x方向[^y]*?间隔\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m`, 'gi'),
    // "间隔3m" anywhere in message when x-direction is present
    new RegExp(`间隔\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m`, 'gi'),
  ]);
}

// Extract bay widths for y-direction (in context of y方向)
function extractBayWidthsY(message: string): number[] | undefined {
  // Check if message has y-direction context
  if (!/y方向|y向/i.test(message)) {
    return undefined;
  }
  return _extractNaturalArray(message, [
    // "间隔3m" after y方向 context
    new RegExp(`y方向[^x]*?间隔\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m`, 'gi'),
    // "间隔3m" when y-direction is explicitly mentioned (with "也是3m" pattern)
    new RegExp(`也是\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m`, 'gi'),
  ]);
}

function extractBayWidths(message: string): number[] | undefined {
  return _extractNaturalArray(message, [
    new RegExp(`(?:跨度|bay\\s*width|span\\s*width)\\s*[：:]*\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)`, 'gi'),
    // English: "single bay 8m" - "bay" followed by number and unit
    new RegExp(`bay\\s*(${DIGIT_PATTERN}(?:\\.${DIGIT_PATTERN})?)\\s*m`, 'gi'),
  ]);
}

function extractFrameDimension(message: string): '2d' | '3d' | undefined {
  // Check for explicit 2D indicators first
  if (/(?:^|[^a-zA-Z])2d|^二维|^平面框架/i.test(message)) {
    return '2d';
  }
  
  // Check for explicit 3D indicators
  if (/(?:^|[^a-zA-Z])3d|^三维|^双方向|^双向框架|x、y向|^x\/y向/i.test(message)) {
    return '3d';
  }
  
  // Check for y-direction indicators (standalone, not part of "x方向")
  if (/(?:^|[^a-zA-Z\u4e00-\u9fa5])y向(?:[^x方向]|$)|(?:^|[^a-zA-Z\u4e00-\u9fa5])y方向(?:[^:：]|$)/i.test(message)) {
    return '3d';
  }
  
  // If x方向 is present with bay count, infer 3D for concrete frames
  if (/x方向.*[1-9](?:[0-9])?(?:跨|bay)/i.test(message)) {
    return '3d';
  }
  
  return undefined;
}

function extractFrameMaterial(message: string): string | undefined {
  const concreteMatch = message.match(/(?:混凝土|concrete)\s*(?:等级|标号|grade)?\s*[：:]*\s*([Cc]\d+)/i);
  if (concreteMatch) return concreteMatch[1].toUpperCase();
  const rebarMatch = message.match(/(?:钢筋|rebar|steel)\s*(?:等级|牌号|grade)?\s*[：:]*\s*([Hh][PpRr][Bb]\d+)/i);
  if (rebarMatch) return rebarMatch[1].toUpperCase();
  const standaloneConcreteMatch = message.match(/(?:^|[^a-zA-Z0-9])([Cc]\d+)(?![0-9])/);
  if (standaloneConcreteMatch) return standaloneConcreteMatch[1].toUpperCase();
  const standaloneRebarMatch = message.match(/(?:^|[^a-zA-Z0-9])([Hh][PpRr][Bb]\d+)(?![0-9])/);
  if (standaloneRebarMatch) return standaloneRebarMatch[1].toUpperCase();
  return undefined;
}

function extractFrameColumnSection(message: string): string | undefined {
  const match = message.match(/(?:柱|column)\s*(?:截面|section)?\s*[：:]*\s*([\dXx×*]+)/i);
  if (match) return match[1].toUpperCase().replace(/×/g, 'X');
  return undefined;
}

function extractFrameBeamSection(message: string): string | undefined {
  const match = message.match(/(?:梁|beam)\s*(?:截面|section)?\s*[：:]*\s*([\dXx×*]+)/i);
  if (match) return match[1].toUpperCase().replace(/×/g, 'X');
  return undefined;
}

export function normalizeConcreteFrameNaturalPatch(
  message: string,
  existingState: DraftState | undefined,
): DraftExtraction {
  const storyCount = extractStoryCount(message) ?? existingState?.storyCount;
  let storyHeightsM = extractStoryHeights(message) ?? existingState?.storyHeightsM;
  const bayCount = extractBayCount(message) ?? existingState?.bayCount;
  const bayCountX = extractBayCountX(message) ?? existingState?.bayCountX;
  const bayCountY = extractBayCountY(message) ?? existingState?.bayCountY;
  const bayWidthsM = extractBayWidths(message) ?? existingState?.bayWidthsM;
  let bayWidthsXM = extractBayWidthsX(message) ?? existingState?.bayWidthsXM;
  let bayWidthsYM = extractBayWidthsY(message) ?? existingState?.bayWidthsYM;
  const frameDimension = extractFrameDimension(message) ?? existingState?.frameDimension;
  const frameMaterial = extractFrameMaterial(message) ?? existingState?.frameMaterial as string | undefined;
  const frameColumnSection = extractFrameColumnSection(message) ?? existingState?.frameColumnSection as string | undefined;
  const frameBeamSection = extractFrameBeamSection(message) ?? existingState?.frameBeamSection as string | undefined;

  // Expand storyHeightsM to match storyCount when it represents a uniform value
  // e.g., [3] with storyCount=3 becomes [3, 3, 3]
  if (storyCount !== undefined && storyHeightsM?.length === 1) {
    const uniformHeight = storyHeightsM[0];
    if (uniformHeight !== undefined) {
      storyHeightsM = Array(storyCount).fill(uniformHeight);
    }
  }

  // Expand bayWidthsXM to match bayCountX when it represents a uniform value
  // e.g., [3] with bayCountX=4 becomes [3, 3, 3, 3]
  if (bayCountX !== undefined && bayWidthsXM?.length === 1) {
    const uniformWidth = bayWidthsXM[0];
    if (uniformWidth !== undefined) {
      bayWidthsXM = Array(bayCountX).fill(uniformWidth);
    }
  }

  // Expand bayWidthsYM to match bayCountY when it represents a uniform value
  // e.g., [3] with bayCountY=3 becomes [3, 3, 3]
  if (bayCountY !== undefined && bayWidthsYM?.length === 1) {
    const uniformWidth = bayWidthsYM[0];
    if (uniformWidth !== undefined) {
      bayWidthsYM = Array(bayCountY).fill(uniformWidth);
    }
  }

  return {
    ...(storyCount !== undefined && { storyCount }),
    ...(storyHeightsM !== undefined && { storyHeightsM }),
    ...(bayCount !== undefined && { bayCount }),
    ...(bayCountX !== undefined && { bayCountX }),
    ...(bayCountY !== undefined && { bayCountY }),
    ...(bayWidthsM !== undefined && { bayWidthsM }),
    ...(bayWidthsXM !== undefined && { bayWidthsXM }),
    ...(bayWidthsYM !== undefined && { bayWidthsYM }),
    ...(frameDimension !== undefined && { frameDimension }),
    ...(frameMaterial !== undefined && { frameMaterial }),
    ...(frameColumnSection !== undefined && { frameColumnSection }),
    ...(frameBeamSection !== undefined && { frameBeamSection }),
  };
}
