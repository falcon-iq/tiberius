/**
 * Step 3: Goals
 */

import { useState, useCallback, useEffect } from 'react';
import { Plus, Trash2, Loader2 } from 'lucide-react';
import { useGoals, useAddGoal, useDeleteGoal } from '@hooks/use-goals';
import type { Step3Props, Goal } from './types';

export const StepGoals = ({ onBack, onNext }: Step3Props) => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [newGoal, setNewGoal] = useState('');
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const { data: existingGoals, isLoading } = useGoals();
  const addGoalMutation = useAddGoal();
  const deleteGoalMutation = useDeleteGoal();

  // Hydrate existing goals from database
  useEffect(() => {
    if (existingGoals && existingGoals.length > 0) {
      setGoals((prev) => {
        const existingGoalTexts = new Set(prev.map((g: Goal) => g.goal.toLowerCase()));
        const newGoals = existingGoals.filter(
          (goal: Goal) => !existingGoalTexts.has(goal.goal.toLowerCase())
        );
        return [...prev, ...newGoals];
      });
    }
  }, [existingGoals]);

  const handleAddGoal = useCallback(() => {
    const trimmedGoal = newGoal.trim();

    if (!trimmedGoal) {
      return;
    }

    setGoals((prev) => {
      const isDuplicate = prev.some(
        (goal) => goal.goal.toLowerCase() === trimmedGoal.toLowerCase()
      );

      if (isDuplicate) {
        setDuplicateError(`"${trimmedGoal}" has already been added`);
        return prev;
      }

      setDuplicateError(null);
      // Create a temporary goal object with local ID for UI
      const tempGoal: Goal = {
        id: Date.now(), // Temporary ID for local state
        goal: trimmedGoal,
        start_date: new Date().toISOString(),
        end_date: null,
      };
      return [...prev, tempGoal];
    });
    setNewGoal('');
  }, [newGoal]);

  const handleRemoveGoal = useCallback(
    async (goalToRemove: Goal) => {
      setGoals((prev) => prev.filter((goal) => goal.id !== goalToRemove.id));

      // Only delete from database if it's an existing goal (not a temp one)
      const existingGoal = existingGoals?.find((g) => g.id === goalToRemove.id);
      if (existingGoal) {
        try {
          await deleteGoalMutation.mutateAsync(existingGoal.id);
        } catch (error) {
          console.error('Failed to delete goal from database:', error);
        }
      }
    },
    [existingGoals, deleteGoalMutation]
  );

  const handleNext = useCallback(async () => {
    setIsSaving(true);

    try {
      // Save all new goals to database
      const existingGoalIds = existingGoals?.map((g: Goal) => g.id) || [];
      const newGoals = goals.filter((goal: Goal) => !existingGoalIds.includes(goal.id));

      for (const goal of newGoals) {
        await addGoalMutation.mutateAsync({
          goal: goal.goal,
          end_date: goal.end_date,
        });
      }

      onNext();
    } catch (error) {
      console.error('Failed to save goals:', error);
    } finally {
      setIsSaving(false);
    }
  }, [goals, existingGoals, addGoalMutation, onNext]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Step 3: Add Goals
        </h2>
        <div className="mb-4">
          <div className="relative flex gap-2">
            <div className="relative flex-1">
              <input
                id="wizard-new-goal"
                type="text"
                value={newGoal}
                onChange={(e) => {
                  setNewGoal(e.target.value);
                  setDuplicateError(null);
                }}
                onKeyDown={(e) => e.key === 'Enter' && handleAddGoal()}
                placeholder="Enter a goal"
                className={`w-full rounded-lg border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
                  duplicateError
                    ? 'border-destructive focus:ring-destructive'
                    : 'border-border focus:ring-primary'
                }`}
              />
            </div>

            <button
              onClick={handleAddGoal}
              disabled={!newGoal.trim()}
              className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              type="button"
              aria-label="Add goal"
            >
              <Plus className="h-5 w-5" />
            </button>
          </div>

          <div className="mt-2 min-h-[20px]">
            {duplicateError ? (
              <p className="text-xs text-destructive">{duplicateError}</p>
            ) : null}
          </div>
        </div>

        {/* Goals List */}
        <div className="space-y-2">
          {isLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}
          {!isLoading && goals.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No goals added yet
            </p>
          )}
          {!isLoading &&
            goals.map((goal) => (
              <div
                key={goal.id}
                className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3"
              >
                <div className="flex-1">
                  <span className="text-sm font-medium text-foreground">{goal.goal}</span>
                </div>
                <button
                  onClick={() => void handleRemoveGoal(goal)}
                  className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
                  type="button"
                  aria-label={`Remove ${goal.goal}`}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="rounded-lg border border-border bg-background px-6 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          type="button"
        >
          Back
        </button>
        <button
          onClick={() => void handleNext()}
          disabled={isSaving}
          className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          type="button"
        >
          {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
          {isSaving ? 'Saving...' : 'Next'}
        </button>
      </div>
    </div>
  );
};
