import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import type { LegalTask, Response } from '../../../types/index';

interface TaskDisplayProps {
  task: LegalTask;
  response: Response;
}

function formatTaskInput(taskType: string, inputData: any) {
  switch (taskType) {
    case 'QA':
      return (
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Question</div>
            <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-blue-500">
              {inputData.question}
            </div>
          </div>
          {inputData.context && (
            <div>
              <div className="text-sm font-medium text-slate-300 mb-1">Context</div>
              <div className="text-slate-200 bg-slate-800/50 p-3 rounded text-sm">
                {inputData.context}
              </div>
            </div>
          )}
        </div>
      );

    case 'STATUTORY_RULE_QA':
      return (
        <div className="space-y-4">
          {/* Main Question */}
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">📋 Legal Question</div>
            <div className="text-slate-100 bg-slate-800 p-4 rounded border-l-4 border-purple-500">
              {inputData.question || 'No question provided'}
            </div>
          </div>

          {/* Rule Reference */}
          {inputData.rule_id && (
            <div>
              <div className="text-sm font-medium text-slate-300 mb-1">⚖️ Legal Rule Reference</div>
              <div className="bg-purple-900/30 p-3 rounded border border-purple-700">
                <code className="text-purple-300 text-sm">{inputData.rule_id}</code>
              </div>
            </div>
          )}

          {/* Legal Context */}
          {inputData.context_full && (
            <div>
              <div className="text-sm font-medium text-slate-300 mb-1">📚 Legal Context</div>
              <div className="text-slate-200 bg-slate-800/50 p-3 rounded text-sm max-h-32 overflow-y-auto">
                {inputData.context_full}
              </div>
            </div>
          )}

          {/* Relevant Articles */}
          {inputData.relevant_articles && (
            <div>
              <div className="text-sm font-medium text-slate-300 mb-1">📖 Relevant Articles</div>
              <div className="bg-blue-900/20 p-3 rounded border border-blue-700">
                <div className="text-blue-300 text-sm">{inputData.relevant_articles}</div>
              </div>
            </div>
          )}

          {/* Category and Tags */}
          <div className="flex flex-wrap gap-2">
            {inputData.category && (
              <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs font-medium">
                📂 {inputData.category}
              </span>
            )}
            {inputData.tags && (
              <span className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded text-xs font-medium">
                🏷️ {inputData.tags}
              </span>
            )}
          </div>

          {/* Additional Metadata */}
          {inputData.metadata_full && (
            <div>
              <div className="text-sm font-medium text-slate-300 mb-1">🔍 Additional Information</div>
              <div className="bg-slate-900 p-3 rounded border border-slate-700">
                <pre className="text-xs text-slate-300 overflow-auto max-h-24">
                  {typeof inputData.metadata_full === 'string' 
                    ? inputData.metadata_full 
                    : JSON.stringify(inputData.metadata_full, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      );

    case 'CLASSIFICATION':
      return (
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Text to Classify</div>
            <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-green-500">
              {inputData.text}
            </div>
          </div>
          {inputData.unit && (
            <div>
              <div className="text-sm font-medium text-slate-300 mb-1">Unit Type</div>
              <span className="inline-block bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs font-medium">
                {inputData.unit}
              </span>
            </div>
          )}
        </div>
      );

    case 'SUMMARIZATION':
      return (
        <div>
          <div className="text-sm font-medium text-slate-300 mb-1">Document to Summarize</div>
          <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-purple-500 max-h-48 overflow-y-auto">
            {inputData.document}
          </div>
        </div>
      );

    case 'PREDICTION':
      return (
        <div>
          <div className="text-sm font-medium text-slate-300 mb-1">Case Facts</div>
          <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-orange-500">
            {inputData.facts}
          </div>
        </div>
      );

    case 'NLI':
      return (
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Premise</div>
            <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-indigo-500">
              {inputData.premise}
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Hypothesis</div>
            <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-pink-500">
              {inputData.hypothesis}
            </div>
          </div>
        </div>
      );

    case 'NER':
      return (
        <div>
          <div className="text-sm font-medium text-slate-300 mb-1">Tokens to Tag</div>
          <div className="bg-slate-800 p-3 rounded border-l-4 border-yellow-500">
            <div className="flex flex-wrap gap-1">
              {(inputData.tokens || []).map((token: string, idx: number) => (
                <span key={idx} className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded text-sm">
                  {token}
                </span>
              ))}
            </div>
          </div>
        </div>
      );

    case 'DRAFTING':
      return (
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Source Text</div>
            <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-red-500">
              {inputData.source}
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Instruction</div>
            <div className="text-slate-200 bg-slate-800/50 p-3 rounded text-sm">
              {inputData.instruction}
            </div>
          </div>
        </div>
      );

    case 'RISK_SPOTTING':
      return (
        <div>
          <div className="text-sm font-medium text-slate-300 mb-1">Text to Analyze</div>
          <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-red-600">
            {inputData.text}
          </div>
        </div>
      );

    case 'DOCTRINE_APPLICATION':
      return (
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Facts</div>
            <div className="text-slate-100 bg-slate-800 p-3 rounded border-l-4 border-cyan-500">
              {inputData.facts}
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">Question</div>
            <div className="text-slate-200 bg-slate-800/50 p-3 rounded text-sm">
              {inputData.question}
            </div>
          </div>
        </div>
      );

    default:
      return (
        <div className="bg-slate-800 p-3 rounded">
          <pre className="text-xs text-slate-200 overflow-auto">
            {JSON.stringify(inputData, null, 2)}
          </pre>
        </div>
      );
  }
}

function formatAIResponse(taskType: string, outputData: any) {
  if (!outputData) {
    return (
      <div className="text-slate-400 italic text-center py-4">
        No AI response available
      </div>
    );
  }

  // Handle common response structure
  if (outputData.response_text) {
    return (
      <div className="space-y-3">
        <div className="text-slate-100 bg-slate-900 p-4 rounded border border-slate-700">
          {outputData.response_text}
        </div>
        {outputData.confidence && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Confidence:</span>
            <div className="flex-1 bg-slate-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${(outputData.confidence || 0) * 100}%` }}
              />
            </div>
            <span className="text-sm text-slate-300">{((outputData.confidence || 0) * 100).toFixed(1)}%</span>
          </div>
        )}
        {outputData.reasoning && (
          <div>
            <div className="text-sm font-medium text-slate-300 mb-1">AI Reasoning</div>
            <div className="text-slate-200 bg-slate-800/50 p-3 rounded text-sm border-l-4 border-slate-600">
              {outputData.reasoning}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Fallback to JSON display for unstructured responses
  return (
    <div className="bg-slate-900 p-3 rounded border border-slate-700">
      <pre className="text-xs text-slate-200 overflow-auto">
        {JSON.stringify(outputData, null, 2)}
      </pre>
    </div>
  );
}

export function TaskDisplay({ task, response }: TaskDisplayProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            📋 Task Input
            <span className="text-sm font-normal bg-slate-700 px-2 py-1 rounded">
              {task.task_type}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {formatTaskInput(task.task_type, task.input_data)}
        </CardContent>
      </Card>

      <Card className="border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            🤖 AI Response
            {response.model_used && (
              <span className="text-sm font-normal bg-blue-700/20 text-blue-400 px-2 py-1 rounded">
                {response.model_used}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {formatAIResponse(task.task_type, response.output_data)}
        </CardContent>
      </Card>
    </div>
  );
}