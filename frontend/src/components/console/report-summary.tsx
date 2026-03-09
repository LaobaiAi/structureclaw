import ReactMarkdown from 'react-markdown'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

export interface ReportSummaryProps {
  report?: { summary?: string; markdown?: string }
}

/**
 * ReportSummary renders markdown report content using react-markdown
 */
export function ReportSummary({ report }: ReportSummaryProps) {
  if (!report || (!report.summary && !report.markdown)) {
    return null
  }

  const content = report.summary || report.markdown || ''

  return (
    <Card>
      <CardHeader>
        <CardTitle>Report</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  )
}
