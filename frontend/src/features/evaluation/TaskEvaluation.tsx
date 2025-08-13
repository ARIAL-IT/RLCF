import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Button } from '@components/ui/Button';
import { useTasks, useFeedback, useSubmitFeedback, useDevilsAdvocateAssignment } from '@hooks/useApi';
import { apiClient } from '../../lib/api';
import { useUIStore } from '../../app/store/ui';
import type { LegalTask, Response } from '../../types/index';
import { EvaluationWizard } from './components/EvaluationWizard';
import { toast } from 'sonner';

export function TaskEvaluation() {
  const navigate = useNavigate();
  const { data: tasks } = useTasks({ status: 'BLIND_EVALUATION' } as any);
  const { selectedTask: storeSelectedTask, setSelectedTask } = useUIStore();
  const [selectedResponse, setSelectedResponse] = useState<Response | null>(null);
  const [loadingResponse, setLoadingResponse] = useState(false);

  // Use the task from the store if available, otherwise pick first available task
  const selectedTask = storeSelectedTask || (tasks && tasks.length > 0 ? tasks[0] : null);

  // Update the store if we're using a fallback task
  useEffect(() => {
    if (!storeSelectedTask && tasks && tasks.length > 0) {
      setSelectedTask(tasks[0]);
    }
  }, [tasks, storeSelectedTask, setSelectedTask]);

  // Load response for selected task
  useEffect(() => {
    if (!selectedTask) {
      setSelectedResponse(null);
      return;
    }

    const loadResponse = async () => {
      setLoadingResponse(true);
      try {
        const responses = await apiClient.responses.list(selectedTask.id);
        if (responses && responses.length > 0) {
          setSelectedResponse(responses[0]);
        } else {
          // Create placeholder response if none exists
          const placeholderResponse: Response = {
            id: selectedTask.id * 1000 + 1,
            task_id: selectedTask.id,
            model_version: 'ai-model-v1',
            output_data: {
              message: 'This is a placeholder AI response for evaluation.',
              confidence: 0.75,
              reasoning: 'Generated for demonstration purposes.'
            },
            generated_at: new Date().toISOString(),
          };
          setSelectedResponse(placeholderResponse);
        }
      } catch (error) {
        console.error('Failed to load response:', error);
        toast.error('Failed to load AI response');
      } finally {
        setLoadingResponse(false);
      }
    };

    loadResponse();
  }, [selectedTask]);

  const isReady = useMemo(() => selectedTask && selectedResponse, [selectedTask, selectedResponse]);

  // Devil's advocate assignment
  const { data: daAssignment } = useDevilsAdvocateAssignment(selectedTask?.id || 0);
  const isDevilsAdvocate = !!daAssignment?.is_assigned;

  const submitFeedback = useSubmitFeedback();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Task Evaluation</h1>
          <p className="text-slate-400">Evaluate AI responses for legal tasks</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              if (!tasks || tasks.length === 0) return;
              const idx = selectedTask ? tasks.findIndex((t) => t.id === selectedTask.id) : -1;
              const next = tasks[(idx + 1) % tasks.length];
              setSelectedTask(next);
              setSelectedResponse(null);
            }}
            disabled={!tasks || tasks.length <= 1}
          >
            Next Task
          </Button>
        </div>
      </div>

      {!tasks || tasks.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No tasks available for evaluation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-400">
              There are currently no tasks in BLIND_EVALUATION status. 
              Contact an admin to create new tasks for evaluation.
            </p>
          </CardContent>
        </Card>
      ) : selectedTask && (loadingResponse || !selectedResponse) ? (
        <Card>
          <CardHeader>
            <CardTitle>Loading Task Response...</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-slate-400 flex items-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-violet-500 border-t-transparent rounded-full"></div>
              Loading AI response for evaluation
            </div>
          </CardContent>
        </Card>
      ) : isReady && selectedTask && selectedResponse ? (
        <EvaluationWizard
          task={selectedTask}
          response={selectedResponse}
          isDevilsAdvocate={isDevilsAdvocate}
          onComplete={(feedback) => {
            submitFeedback.mutate(
              { responseId: selectedResponse.id, feedbackData: feedback },
              {
                onSuccess: () => {
                  toast.success('Feedback submitted successfully!');
                  // Move to next task automatically
                  if (tasks && tasks.length > 1) {
                    const idx = tasks.findIndex((t) => t.id === selectedTask.id);
                    const next = tasks[(idx + 1) % tasks.length];
                    setSelectedTask(next);
                  }
                },
                onError: (error) => {
                  toast.error('Failed to submit feedback. Please try again.');
                  console.error('Submission error:', error);
                }
              }
            );
          }}
        />
      ) : null}

      {/* Task Info Panel */}
      {selectedTask && (
        <Card>
          <CardHeader>
            <CardTitle>Current Task Info</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-400">Task ID:</span> {selectedTask.id}
              </div>
              <div>
                <span className="text-slate-400">Type:</span> {selectedTask.task_type}
              </div>
              <div>
                <span className="text-slate-400">Status:</span> {selectedTask.status}
              </div>
              <div>
                <span className="text-slate-400">Devil's Advocate:</span> {isDevilsAdvocate ? 'Yes' : 'No'}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}