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
import { useEvaluationStore } from '../../../app/store/evaluation';
import { TaskDisplay } from './TaskDisplay';
import { EditableTaskInput } from './EditableTaskInput';
import { QualityScoring } from './QualityScoring';
import { EvaluationProgress } from './EvaluationProgress';
import { EvaluationSummary } from './EvaluationSummary';

interface EvaluationWizardProps {
  task: LegalTask;
  response: Response;
  isDevilsAdvocate?: boolean;
  onComplete: (feedback: FeedbackData) => void;
}

function ConfidenceSlider({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="space-y-2 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <div className="flex items-center justify-between">
        <label className="font-medium text-slate-200">Confidence in Your Evaluation</label>
        <span className="font-bold text-lg text-cyan-400">{value}/10</span>
      </div>
      <p className="text-sm text-slate-400">How confident are you in the accuracy and completeness of your assessment?</p>
      <input
        type="range"
        min="1"
        max="10"
        step="1"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
      />
    </div>
  );
}

export function EvaluationWizard({ task, response, isDevilsAdvocate = false, onComplete }: EvaluationWizardProps) {
  const { user } = useAuthStore();
  const {
    currentEvaluation,
    startEvaluation,
    nextStep,
    previousStep,
    setFormData,
    goToStep,
  } = useEvaluationStore();

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [scores, setScores] = useState({ accuracy: 8, utility: 8, transparency: 8 });
  const [evaluatorConfidence, setEvaluatorConfidence] = useState(8);
  const [editedTaskInput, setEditedTaskInput] = useState(task.input_data);
  const [hasTaskInputChanges, setHasTaskInputChanges] = useState(false);
  const [interactions, setInteractions] = useState<number>(0);
  const incInteractions = () => setInteractions((n) => n + 1);

  useEffect(() => {
    if (!currentEvaluation || currentEvaluation.taskId !== task.id) {
      startEvaluation(task, response, isDevilsAdvocate);
    }
  }, [task, response, isDevilsAdvocate, startEvaluation, currentEvaluation]);

  const step = currentEvaluation?.currentStep ?? 1;

  const baseSchema = useMemo(() => getSchemaForTaskType(task.task_type), [task.task_type]);
  const fullSchema = useMemo(() => {
    if (!isDevilsAdvocate) return baseSchema;
    return baseSchema.and(
      z.object({
        devils_advocate: z.object({
          critical_findings: z.string().min(10, 'Provide critical findings (min 10 chars)'),
          alternative_positions: z.array(z.string()).optional(),
        }).strict(),
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
    defaultValues: currentEvaluation?.formData ?? {},
    mode: 'onChange',
  });

  useEffect(() => {
    const subscription = watch((value) => {
      setFormData(value);
    });
    return () => subscription.unsubscribe();
  }, [watch, setFormData]);

  useEffect(() => {
    if (currentEvaluation?.formData) {
      reset(currentEvaluation.formData);
    }
  }, [currentEvaluation?.taskId, reset]);

  const { data: prompts } = useDevilsAdvocatePrompts(task.task_type);

  const onSubmit = (data: FormValues) => {
    if (!user || !currentEvaluation) {
      setSubmitError('User or evaluation session not found.');
      return;
    }
    setSubmitError(null);

    const feedbackPayload: FeedbackData = {
      user_id: user.id,
      accuracy_score: scores.accuracy,
      utility_score: scores.utility,
      transparency_score: scores.transparency,
      feedback_data: {
        ...data,
        ...(hasTaskInputChanges && {
          corrected_task_input: editedTaskInput,
        }),
      },
      metadata: {
        time_spent_ms: Date.now() - currentEvaluation.startTime,
        interactions,
        evaluator_confidence: evaluatorConfidence / 10,
        is_devils_advocate: isDevilsAdvocate,
        task_input_modified: hasTaskInputChanges,
      },
    };

    try {
      onComplete(feedbackPayload);
      const successStep = isDevilsAdvocate ? 6 : 5;
      goToStep(successStep);
    } catch (e: any) {
      setSubmitError(e?.message ?? 'Submit failed');
    }
  };
  
  const maxSteps = isDevilsAdvocate ? 5 : 4;

  if (!currentEvaluation) {
    return <div>Loading evaluation...</div>;
  }

  return (
    <div className="space-y-6">
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🎯</span>
              <div>
                <div className="text-xl">Evaluation Wizard</div>
                <div className="text-sm font-normal text-slate-400">
                  Task #{task.id} • {task.task_type}
                  {isDevilsAdvocate && (
                    <span className="ml-2 bg-red-500/20 text-red-400 px-2 py-1 rounded text-xs">
                      😈 Devil's Advocate
                    </span>
                  )}
                </div>
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EvaluationProgress 
            currentStep={step}
            totalSteps={maxSteps}
            isDevilsAdvocate={isDevilsAdvocate}
          />
        </CardContent>
      </Card>

      {step === 1 && (
        <div className="space-y-6" onClick={incInteractions}>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <EditableTaskInput 
              task={{...task, input_data: editedTaskInput}} 
              onInputChange={(updatedData) => {
                setEditedTaskInput(updatedData);
                setHasTaskInputChanges(true);
              }}
            />
            <TaskDisplay task={{...task, input_data: editedTaskInput}} response={response} />
          </div>
          <div className="flex justify-end gap-2">
            <Button onClick={nextStep} size="lg">
              Continue to Evaluation →
            </Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <Card className="border-slate-700">
          <CardHeader>
            <CardTitle>📝 Blind Evaluation</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-6"
              onSubmit={(e) => {
                incInteractions();
                e.preventDefault();
                handleSubmit(() => nextStep())();
              }}
            >
              <TaskFormFields taskType={task.task_type} register={register} setValue={setValue} errors={errors} />
              <div className="flex justify-between gap-2 pt-4 border-t border-slate-700">
                <Button variant="secondary" type="button" onClick={previousStep}>
                  ← Back
                </Button>
                <Button type="submit" size="lg">
                  Continue to Scoring →
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <div className="space-y-6" onClick={incInteractions}>
          <QualityScoring scores={scores} onScoreChange={setScores} />
          <div className="flex justify-between gap-2">
            <Button variant="secondary" onClick={previousStep} size="lg">
              ← Back
            </Button>
            <Button onClick={nextStep} size="lg">
              {isDevilsAdvocate ? "Continue to Devil's Advocate →" : 'Continue to Review →'}
            </Button>
          </div>
        </div>
      )}

      {step === 4 && isDevilsAdvocate && (
        <Card className="border-red-700 bg-red-950/20">
          <CardHeader>
            <CardTitle className="text-red-400">😈 Devil's Advocate Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6" onClick={incInteractions}>
            {prompts && prompts.length > 0 && (
              <div className="p-4 bg-red-900/20 rounded-md border border-red-700">
                <ul className="space-y-2 text-sm text-red-200">
                  {prompts.slice(0, 8).map((p, i) => (
                    <li key={i}>• {p}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Critical Findings</label>
                <textarea
                  className="w-full p-3 bg-slate-900 border border-red-700 rounded-md"
                  rows={6}
                  placeholder="Identify issues, biases, or weaknesses..."
                  {...register('devils_advocate.critical_findings' as any)}
                />
                {errors?.devils_advocate?.critical_findings && <p className="text-red-400 text-xs mt-1">{String(errors.devils_advocate.critical_findings.message)}</p>}
              </div>
            </div>
            <div className="flex justify-between gap-2 pt-4 border-t border-red-800">
              <Button variant="secondary" onClick={previousStep} size="lg">
                ← Back
              </Button>
              <Button onClick={nextStep} size="lg" className="bg-red-600 hover:bg-red-700">
                Continue to Review →
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {(step === 4 && !isDevilsAdvocate) || (step === 5 && isDevilsAdvocate) ? (
        <div className="space-y-6" onClick={incInteractions}>
          <Card className="border-slate-700">
            <CardHeader>
              <CardTitle>✅ Review Your Evaluation</CardTitle>
            </CardHeader>
            <CardContent>
              <EvaluationSummary 
                taskType={task.task_type}
                formData={currentEvaluation.formData}
                scores={scores}
                isDevilsAdvocate={isDevilsAdvocate}
              />
              <div className="mt-6">
                <ConfidenceSlider value={evaluatorConfidence} onChange={setEvaluatorConfidence} />
              </div>
              <div className="flex justify-between gap-2 pt-6 border-t border-slate-700 mt-6">
                <Button variant="secondary" onClick={previousStep} size="lg">
                  ← Back to Edit
                </Button>
                <Button 
                  onClick={handleSubmit(onSubmit)} 
                  loading={isSubmitting}
                  size="lg"
                  className="bg-green-600 hover:bg-green-700"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Evaluation ✓'}
                </Button>
              </div>
              {submitError && <div className="mt-4 p-3 bg-red-900/20 border border-red-700 rounded text-red-400 text-sm">{submitError}</div>}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {(step === 5 && !isDevilsAdvocate) || (step === 6 && isDevilsAdvocate) ? (
        <Card className="border-green-700 bg-green-950/20">
          <CardContent className="text-center py-12">
            <div className="space-y-6">
              <div className="text-6xl">🎉</div>
              <div>
                <h3 className="text-2xl font-bold text-green-400 mb-2">Evaluation Submitted!</h3>
                <p className="text-slate-300 text-lg">Thank you for your contribution.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
