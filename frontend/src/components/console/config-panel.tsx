'use client'

import { useStore } from '@/lib/stores/context'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import type { AnalysisType, ReportFormat, ReportOutput } from '@/lib/stores/slices/console'

/**
 * ConfigPanel - Configuration options and checkboxes for console execution
 *
 * CONS-05: User can configure analysis options (analysisType, reportFormat, reportOutput)
 * CONS-06: User can toggle checkboxes (includeModel, autoAnalyze, autoCodeCheck, includeReport)
 */
export function ConfigPanel() {
  const analysisType = useStore((state) => state.analysisType)
  const reportFormat = useStore((state) => state.reportFormat)
  const reportOutput = useStore((state) => state.reportOutput)
  const includeModel = useStore((state) => state.includeModel)
  const autoAnalyze = useStore((state) => state.autoAnalyze)
  const autoCodeCheck = useStore((state) => state.autoCodeCheck)
  const includeReport = useStore((state) => state.includeReport)

  const setAnalysisType = useStore((state) => state.setAnalysisType)
  const setReportFormat = useStore((state) => state.setReportFormat)
  const setReportOutput = useStore((state) => state.setReportOutput)
  const setIncludeModel = useStore((state) => state.setIncludeModel)
  const setAutoAnalyze = useStore((state) => state.setAutoAnalyze)
  const setAutoCodeCheck = useStore((state) => state.setAutoCodeCheck)
  const setIncludeReport = useStore((state) => state.setIncludeReport)

  return (
    <div className="space-y-4">
      {/* Select Options - 3 Column Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Analysis Type Select */}
        <div className="space-y-2">
          <label htmlFor="analysis-type-select" className="text-sm font-medium">
            Analysis Type
          </label>
          <Select
            value={analysisType}
            onValueChange={(value) => setAnalysisType(value as AnalysisType)}
          >
            <SelectTrigger id="analysis-type-select" aria-label="Analysis Type">
              <SelectValue placeholder="Select analysis type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">none</SelectItem>
              <SelectItem value="structural">structural</SelectItem>
              <SelectItem value="code">code</SelectItem>
              <SelectItem value="comprehensive">comprehensive</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Report Format Select */}
        <div className="space-y-2">
          <label htmlFor="report-format-select" className="text-sm font-medium">
            Report Format
          </label>
          <Select
            value={reportFormat}
            onValueChange={(value) => setReportFormat(value as ReportFormat)}
          >
            <SelectTrigger id="report-format-select" aria-label="Report Format">
              <SelectValue placeholder="Select report format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="markdown">markdown</SelectItem>
              <SelectItem value="html">html</SelectItem>
              <SelectItem value="json">json</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Report Output Select */}
        <div className="space-y-2">
          <label htmlFor="report-output-select" className="text-sm font-medium">
            Report Output
          </label>
          <Select
            value={reportOutput}
            onValueChange={(value) => setReportOutput(value as ReportOutput)}
          >
            <SelectTrigger id="report-output-select" aria-label="Report Output">
              <SelectValue placeholder="Select report output" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="inline">inline</SelectItem>
              <SelectItem value="file">file</SelectItem>
              <SelectItem value="both">both</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Checkboxes Row */}
      <div className="flex flex-wrap gap-4">
        {/* Include Model Checkbox */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="include-model"
            aria-label="Include Model"
            checked={includeModel}
            onCheckedChange={(checked) => setIncludeModel(checked === true)}
          />
          <label htmlFor="include-model" className="text-sm font-medium cursor-pointer">
            Include Model
          </label>
        </div>

        {/* Auto Analyze Checkbox */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="auto-analyze"
            aria-label="Auto Analyze"
            checked={autoAnalyze}
            onCheckedChange={(checked) => setAutoAnalyze(checked === true)}
          />
          <label htmlFor="auto-analyze" className="text-sm font-medium cursor-pointer">
            Auto Analyze
          </label>
        </div>

        {/* Auto Code Check Checkbox */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="auto-code-check"
            aria-label="Auto Code Check"
            checked={autoCodeCheck}
            onCheckedChange={(checked) => setAutoCodeCheck(checked === true)}
          />
          <label htmlFor="auto-code-check" className="text-sm font-medium cursor-pointer">
            Auto Code Check
          </label>
        </div>

        {/* Include Report Checkbox */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="include-report"
            aria-label="Include Report"
            checked={includeReport}
            onCheckedChange={(checked) => setIncludeReport(checked === true)}
          />
          <label htmlFor="include-report" className="text-sm font-medium cursor-pointer">
            Include Report
          </label>
        </div>
      </div>
    </div>
  )
}
