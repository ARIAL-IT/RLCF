import { z } from 'zod';
import type { FieldErrors, UseFormRegister, UseFormSetValue } from 'react-hook-form';

// Schemas aligned with backend `task_config.yaml`
export const TASK_FORM_SCHEMAS = {
  QA: z.object({
    validated_answer: z.string().min(10, 'Provide a validated answer (min 10 chars)'),
    position: z.enum(['correct', 'incorrect']),
    reasoning: z.string().min(50, 'Reasoning must be at least 50 chars'),
  }),
  CLASSIFICATION: z.object({
    validated_labels: z.array(z.string()).min(1, 'Select at least one label'),
    reasoning: z.string().min(50, 'Reasoning must be at least 50 chars'),
  }),
  SUMMARIZATION: z.object({
    revised_summary: z.string().min(30, 'Summary must be at least 30 chars'),
    rating: z.enum(['good', 'bad']),
    reasoning: z.string().min(50),
  }),
  PREDICTION: z.object({
    chosen_outcome: z.enum(['violation', 'no_violation']),
    reasoning: z.string().min(50),
  }),
  NLI: z.object({
    chosen_label: z.enum(['entail', 'contradict', 'neutral']),
    reasoning: z.string().min(50),
  }),
  NER: z.object({
    validated_tags: z.array(z.string()).min(1),
    reasoning: z.string().min(30),
  }),
  DRAFTING: z.object({
    revised_target: z.string().min(30),
    rating: z.enum(['better', 'worse']),
    reasoning: z.string().min(50),
  }),
  RISK_SPOTTING: z.object({
    validated_risk_labels: z.array(z.string()).min(1),
    validated_severity: z.number().min(0).max(10),
    reasoning: z.string().min(50),
  }),
  DOCTRINE_APPLICATION: z.object({
    chosen_label: z.enum(['yes', 'no']),
    reasoning: z.string().min(50),
  }),
} as const;

export function getSchemaForTaskType(taskType: string) {
  return TASK_FORM_SCHEMAS[taskType as keyof typeof TASK_FORM_SCHEMAS] ?? z.object({});
}

interface TaskFormFieldsProps {
  taskType: string;
  register: UseFormRegister<any>;
  setValue: UseFormSetValue<any>;
  errors: FieldErrors<any>;
}

export function TaskFormFields({ taskType, register, setValue, errors }: TaskFormFieldsProps) {
  if (taskType === 'QA') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Validated answer</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={5} {...register('validated_answer')} />
          {errors?.validated_answer && <p className="text-red-400 text-xs">{String(errors.validated_answer.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Position</label>
          <select className="w-full p-2 bg-slate-900 border border-slate-700 rounded" {...register('position')}>
            <option value="correct">Correct</option>
            <option value="incorrect">Incorrect</option>
          </select>
          {errors?.position && <p className="text-red-400 text-xs">{String(errors.position.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'CLASSIFICATION') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Validated labels (comma-separated)</label>
          <input
            className="w-full p-2 bg-slate-900 border border-slate-700 rounded"
            onChange={(e) => setValue('validated_labels', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
          />
          {errors?.validated_labels && <p className="text-red-400 text-xs">{String(errors.validated_labels.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'SUMMARIZATION') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Revised summary</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={5} {...register('revised_summary')} />
          {errors?.revised_summary && <p className="text-red-400 text-xs">{String(errors.revised_summary.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Rating</label>
          <select className="w-full p-2 bg-slate-900 border border-slate-700 rounded" {...register('rating')}>
            <option value="good">Good</option>
            <option value="bad">Bad</option>
          </select>
          {errors?.rating && <p className="text-red-400 text-xs">{String(errors.rating.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'PREDICTION') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Chosen outcome</label>
          <select className="w-full p-2 bg-slate-900 border border-slate-700 rounded" {...register('chosen_outcome')}>
            <option value="violation">Violation</option>
            <option value="no_violation">No Violation</option>
          </select>
          {errors?.chosen_outcome && <p className="text-red-400 text-xs">{String(errors.chosen_outcome.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'NLI') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Chosen label</label>
          <select className="w-full p-2 bg-slate-900 border border-slate-700 rounded" {...register('chosen_label')}>
            <option value="entail">Entail</option>
            <option value="contradict">Contradict</option>
            <option value="neutral">Neutral</option>
          </select>
          {errors?.chosen_label && <p className="text-red-400 text-xs">{String(errors.chosen_label.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'NER') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Validated tags (comma-separated)</label>
          <input
            className="w-full p-2 bg-slate-900 border border-slate-700 rounded"
            onChange={(e) => setValue('validated_tags', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
          />
          {errors?.validated_tags && <p className="text-red-400 text-xs">{String(errors.validated_tags.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'DRAFTING') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Revised target</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={5} {...register('revised_target')} />
          {errors?.revised_target && <p className="text-red-400 text-xs">{String(errors.revised_target.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Rating</label>
          <select className="w-full p-2 bg-slate-900 border border-slate-700 rounded" {...register('rating')}>
            <option value="better">Better</option>
            <option value="worse">Worse</option>
          </select>
          {errors?.rating && <p className="text-red-400 text-xs">{String(errors.rating.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'RISK_SPOTTING') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Validated risk labels (comma-separated)</label>
          <input
            className="w-full p-2 bg-slate-900 border border-slate-700 rounded"
            onChange={(e) => setValue('validated_risk_labels', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
          />
          {errors?.validated_risk_labels && <p className="text-red-400 text-xs">{String(errors.validated_risk_labels.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Validated severity (0-10)</label>
          <input
            type="number"
            step="1"
            min="0"
            max="10"
            className="w-full p-2 bg-slate-900 border border-slate-700 rounded"
            {...register('validated_severity', { valueAsNumber: true })}
          />
          {errors?.validated_severity && <p className="text-red-400 text-xs">{String(errors.validated_severity.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  if (taskType === 'DOCTRINE_APPLICATION') {
    return (
      <div className="space-y-3">
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Chosen label</label>
          <select className="w-full p-2 bg-slate-900 border border-slate-700 rounded" {...register('chosen_label')}>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
          {errors?.chosen_label && <p className="text-red-400 text-xs">{String(errors.chosen_label.message)}</p>}
        </div>
        <div className="space-y-1">
          <label className="block text-sm text-slate-300">Reasoning</label>
          <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
          {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
        </div>
      </div>
    );
  }

  // Fallback generic
  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <label className="block text-sm text-slate-300">Reasoning</label>
        <textarea className="w-full p-2 bg-slate-900 border border-slate-700 rounded" rows={6} {...register('reasoning')} />
        {errors?.reasoning && <p className="text-red-400 text-xs">{String(errors.reasoning.message)}</p>}
      </div>
    </div>
  );
}

export type TaskFormSchema = typeof TASK_FORM_SCHEMAS[keyof typeof TASK_FORM_SCHEMAS];
export type TaskFormValues<T extends TaskFormSchema> = z.infer<T>;

