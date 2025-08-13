import { useEffect, useMemo, useRef, useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { LegalTask, Response, FeedbackData } from '../../../types/index';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { useDevilsAdvocatePrompts } from '../../../hooks/useApi';
import { TaskFormFields, getSchemaForTaskType } from '../forms/TaskFormFactory';
import { useAuthStore } from '../../../app/store/auth';

interface EvaluationWizardProps {
  task: LegalTask;
  response: Response;
  isDevilsAdvocate?: boolean;
  onComplete: (feedback: FeedbackData) => void;
}

type WizardStep = 1 | 2 | 3 | 4 | 5 | 6;

export function EvaluationWizard({ task, response, isDevilsAdvocate = false, onComplete }: EvaluationWizardProps) {
  const { user } = useAuthStore();
  const [step, setStep] = useState<WizardStep>(1);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [scores, setScores] = useState({
    accuracy: 8,
    utility: 8,
    transparency: 8,
  });

  const startTimeRef = useRef<number>(Date.now());
  const [interactions, setInteractions] = useState<number>(0);
  const incInteractions = () => setInteractions((n) => n + 1);

  const draftKey = useMemo(
    () => `rlcf_draft_${task.id}_${response.id}`,
    [task.id, response.id]
  );

  const baseSchema = useMemo(() => getSchemaForTaskType(task.task_type), [task.task_type]);

  const fullSchema = useMemo(() => {
    if (!isDevilsAdvocate) return baseSchema;
    return baseSchema.and(
      z.object({
        devils_advocate: z
          .object({
            critical_findings: z.string().min(10, 'Provide critical findings (min 10 chars)'),
            alternative_positions: z.array(z.string()).optional(),
          })
          .strict(),
      })
    );
  }, [baseSchema, isDevilsAdvocate]);

  type FormValues = z.infer<typeof fullSchema>;

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
    watch,
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(fullSchema),
    defaultValues: undefined,
    mode: 'onChange',
  });

  useEffect(() => {
    const raw = localStorage.getItem(draftKey);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        reset(parsed.data);
        setScores(parsed.scores || { accuracy: 8, utility: 8, transparency: 8 });
      } catch {}
    }
  }, [draftKey, reset]);

  const values = watch();
  const saveTimeout = useRef<number | null>(null);
  useEffect(() => {
    if (saveTimeout.current) window.clearTimeout(saveTimeout.current);
    saveTimeout.current = window.setTimeout(() => {
      try {
        localStorage.setItem(draftKey, JSON.stringify({ data: values, scores }));
      } catch {}
    }, 400);
    return () => {
      if (saveTimeout.current) window.clearTimeout(saveTimeout.current);
    };
  }, [values, scores, draftKey]);

  const { data: prompts } = useDevilsAdvocatePrompts(task.task_type);

  const goNext = () =>
    setStep((s) => {
      const next = (s + 1) as WizardStep;
      const maxSteps = isDevilsAdvocate ? 6 : 5;
      return Math.min(next, maxSteps) as WizardStep;
    });
  const goPrev = () =>
    setStep((s) => {
      const prev = (s - 1) as WizardStep;
      return Math.max(prev, 1) as WizardStep;
    });

  const onSubmit = (data: FormValues) => {
    if (!user) {
      setSubmitError('You must be logged in to submit feedback.');
      return;
    }
    setSubmitError(null);

    const feedbackPayload: FeedbackData = {
      user_id: user.id,
      accuracy_score: scores.accuracy,
      utility_score: scores.utility,
      transparency_score: scores.transparency,
      feedback_data: data,
    };

    try {
      onComplete(feedbackPayload);
      localStorage.removeItem(draftKey);
      setStep(isDevilsAdvocate ? 6 : 5);
    } catch (e: any) {
      setSubmitError(e?.message ?? 'Submit failed');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Evaluation Wizard • Task #{task.id} • {task.task_type}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {step === 1 && (
          <div className="space-y-4" onClick={incInteractions}>
            <h3 className="text-white font-medium">Review Task and AI Response</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-800 rounded-md border border-slate-700">
                <div className="text-slate-400 text-sm mb-2">Task Input</div>
                <pre className="text-xs text-slate-200 overflow-auto max-h-64">
                  {JSON.stringify(task.input_data, null, 2)}
                </pre>
              </div>
              <div className="p-4 bg-slate-800 rounded-md border border-slate-700">
                <div className="text-slate-400 text-sm mb-2">AI Response</div>
                <pre className="text-xs text-slate-200 overflow-auto max-h-64">
                  {JSON.stringify(response.output_data, null, 2)}
                </pre>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button onClick={goNext}>Next</Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <form
            className="space-y-4"
            onSubmit={(e) => {
              incInteractions();
              e.preventDefault();
              handleSubmit(() => goNext())();
            }}
          >
            <h3 className="text-white font-medium">Blind Evaluation</h3>
            <TaskFormFields taskType={task.task_type} register={register} setValue={setValue} errors={errors} />
            <div className="flex justify-between gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={goPrev}>Back</Button>
              <Button type="submit">Continue</Button>
            </div>
          </form>
        )}

        {step === 3 && (
          <div className="space-y-4" onClick={incInteractions}>
            <h3 className="text-white font-medium">Quality Scoring</h3>
            <div className="space-y-3">
              <label className="block text-sm text-slate-300">Accuracy ({scores.accuracy}/10)</label>
              <input type="range" min="1" max="10" value={scores.accuracy} onChange={(e) => setScores(s => ({...s, accuracy: +e.target.value}))} className="w-full" />
            </div>
            <div className="space-y-3">
              <label className="block text-sm text-slate-300">Utility ({scores.utility}/10)</label>
              <input type="range" min="1" max="10" value={scores.utility} onChange={(e) => setScores(s => ({...s, utility: +e.target.value}))} className="w-full" />
            </div>
            <div className="space-y-3">
              <label className="block text-sm text-slate-300">Transparency ({scores.transparency}/10)</label>
              <input type="range" min="1" max="10" value={scores.transparency} onChange={(e) => setScores(s => ({...s, transparency: +e.target.value}))} className="w-full" />
            </div>
            <div className="flex justify-between gap-2 pt-2">
              <Button variant="secondary" onClick={goPrev}>Back</Button>
              <Button onClick={goNext}>Continue</Button>
            </div>
          </div>
        )}

        {step === 4 && isDevilsAdvocate && (
          <div className="space-y-3" onClick={incInteractions}>
            <h3 className="text-white font-medium">Devil's Advocate</h3>
            {prompts && prompts.length > 0 && (
              <div className="p-3 bg-slate-800 rounded-md border border-slate-700">
                <div className="text-slate-400 text-sm mb-2">Critical prompts</div>
                <ul className="list-disc pl-5 text-sm text-slate-200">
                  {prompts.slice(0, 8).map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="space-y-2">
              <label className="block text-sm text-slate-300">Critical findings</label>
              <textarea
                className="w-full p-2 bg-slate-900 border border-slate-700 rounded"
                rows={6}
                {...register('devils_advocate.critical_findings' as any)}
              />
              {errors && (errors as any)?.devils_advocate?.critical_findings && (
                <p className="text-red-400 text-xs">{String((errors as any).devils_advocate.critical_findings.message)}</p>
              )}
            </div>
            <div className="space-y-2">
              <label className="block text-sm text-slate-300">Alternative positions (comma-separated)</label>
              <input
                className="w-full p-2 bg-slate-900 border border-slate-700 rounded"
                onChange={(e) => setValue('devils_advocate.alternative_positions' as any, e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
              />
            </div>
            <div className="flex justify-between gap-2 pt-2">
              <Button variant="secondary" onClick={goPrev}>Back</Button>
              <Button onClick={goNext}>Continue</Button>
            </div>
          </div>
        )}

        {((step === 4 && !isDevilsAdvocate) || (step === 5 && isDevilsAdvocate)) && (
          <div className="space-y-4" onClick={incInteractions}>
            <h3 className="text-white font-medium">Confirmation</h3>
            <div className="p-3 bg-slate-800 rounded-md border border-slate-700">
              <div className="text-slate-400 text-sm mb-2">Your feedback</div>
              <pre className="text-xs text-slate-200 overflow-auto max-h-64">{JSON.stringify({ scores, ...values }, null, 2)}</pre>
            </div>
            <div className="flex justify-between gap-2">
              <Button variant="secondary" onClick={goPrev}>Back</Button>
              <Button onClick={() => handleSubmit(onSubmit)()} loading={isSubmitting}>Submit</Button>
            </div>
            {submitError && <p className="text-red-400 text-sm">{submitError}</p>}
          </div>
        )}

        {((step === 5 && !isDevilsAdvocate) || (step === 6 && isDevilsAdvocate)) && (
          <div className="space-y-3 text-center">
            <h3 className="text-green-400 font-semibold">Feedback submitted</h3>
            <p className="text-slate-400 text-sm">Thank you for your evaluation.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

