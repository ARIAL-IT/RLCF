import { useEffect, useMemo, useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { LegalTask, Response, FeedbackData } from '../../../types/index';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { useDevilsAdvocatePrompts } from '../../../hooks/useApi';
import { TaskFormFields, getSchemaForTaskType } from '../forms/TaskFormFactory';
import { PreferenceForm, preferenceSchema } from '../forms/PreferenceForm';
import { useAuthStore } from '../../../app/store/auth';
import { useEvaluationStore } from '../../../app/store/evaluation';
import { TaskDisplay } from './TaskDisplay';
import { EditableTaskInput } from './EditableTaskInput';
import { QualityScoring } from './QualityScoring';
import { EvaluationProgress } from './EvaluationProgress';
import { EvaluationSummary } from './EvaluationSummary';

interface EvaluationWizardProps {
  task: LegalTask;
  mode: 'standard' | 'preference';
  responseA: Response;
  responseB?: Response | null;
  isDevilsAdvocate?: boolean;
  onComplete: (feedback: FeedbackData) => void;
}

export function EvaluationWizard({ task, mode, responseA, responseB, isDevilsAdvocate = false, onComplete }: EvaluationWizardProps) {
  const { user } = useAuthStore();
  const { currentEvaluation, startEvaluation, nextStep, previousStep, setFormData, goToStep } = useEvaluationStore();

  const [scores, setScores] = useState({ accuracy: 8, utility: 8, transparency: 8 });
  const [editedTaskInput, setEditedTaskInput] = useState(task.input_data);
  const [hasTaskInputChanges, setHasTaskInputChanges] = useState(false);

  useEffect(() => {
    if (!currentEvaluation || currentEvaluation.taskId !== task.id) {
      startEvaluation(task, responseA, isDevilsAdvocate);
    }
  }, [task, responseA, isDevilsAdvocate, startEvaluation, currentEvaluation]);

  const step = currentEvaluation?.currentStep ?? 1;

  const schema = useMemo(() => 
    mode === 'preference' ? preferenceSchema : getSchemaForTaskType(task.task_type),
    [mode, task.task_type]
  );

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
    watch,
    reset,
  } = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: currentEvaluation?.formData ?? {},
  });

  useEffect(() => {
    const subscription = watch((value) => setFormData(value));
    return () => subscription.unsubscribe();
  }, [watch, setFormData]);

  useEffect(() => {
    if (currentEvaluation?.taskId !== task.id) {
      reset({});
    }
  }, [currentEvaluation?.taskId, task.id, reset]);

  const onSubmit = (data: z.infer<typeof schema>) => {
    if (!user || !currentEvaluation) return;

    const feedbackPayload: FeedbackData = {
      user_id: user.id,
      accuracy_score: scores.accuracy,
      utility_score: scores.utility,
      transparency_score: scores.transparency,
      feedback_data: { ...data },
      metadata: {
        mode,
        time_spent_ms: Date.now() - currentEvaluation.startTime,
        task_input_modified: hasTaskInputChanges,
        ...(mode === 'preference' && { response_a_id: responseA.id, response_b_id: responseB?.id }),
      },
    };
    onComplete(feedbackPayload);
    goToStep(3); // Go to success step
  };

  if (!currentEvaluation) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle>Evaluation Wizard</CardTitle>
        </CardHeader>
        <CardContent>
          <EvaluationProgress currentStep={step} totalSteps={2} />
        </CardContent>
      </Card>

      {step === 1 && (
        <div className="space-y-6">
          <TaskDisplay 
            task={task} 
            mode={mode} 
            responseA={responseA} 
            responseB={responseB} 
          />
          <div className="flex justify-end">
            <Button onClick={nextStep} size="lg">Continue to Evaluation →</Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <Card className="border-slate-700">
          <CardHeader>
            <CardTitle>{mode === 'preference' ? 'Compare and Decide' : 'Blind Evaluation'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {mode === 'preference' ? (
                <PreferenceForm register={register} errors={errors} />
              ) : (
                <TaskFormFields taskType={task.task_type} register={register} setValue={setValue} errors={errors} />
              )}
              <div className="mt-4">
                <h3 className="text-lg font-medium text-slate-200 mb-4">Quality Scoring</h3>
                <QualityScoring scores={scores} onScoreChange={setScores} />
              </div>
              <div className="flex justify-between gap-2 pt-4 border-t border-slate-700">
                <Button variant="secondary" type="button" onClick={previousStep}>← Back</Button>
                <Button type="submit" size="lg" loading={isSubmitting} className="bg-green-600 hover:bg-green-700">Submit Evaluation ✓</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card className="border-green-700 bg-green-950/20">
          <CardContent className="text-center py-12">
            <div className="text-6xl">🎉</div>
            <h3 className="text-2xl font-bold text-green-400 mt-4">Evaluation Submitted!</h3>
          </CardContent>
        </Card>
      )}
    </div>
  );
}