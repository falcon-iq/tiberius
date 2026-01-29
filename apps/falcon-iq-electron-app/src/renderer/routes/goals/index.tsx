import { createFileRoute } from '@tanstack/react-router';
import { useState, useMemo } from 'react';
import { Plus, CheckCircle2, Loader2, Trash2, RotateCcw } from 'lucide-react';
import { useGoals, useAddGoal, useUpdateGoal, useDeleteGoal } from '@hooks/use-goals';
import { formatDate, getCurrentTimestamp, getTodayDateInputValue, dateInputToISO } from '@libs/shared/utils/date';
import { Modal } from '@libs/shared/ui/modal';
import { Tooltip } from '@libs/shared/ui/tooltip';

export const Route = createFileRoute('/goals/')({
  component: GoalsPage,
});

type FilterType = 'all' | 'current' | 'past';

function GoalsPage() {
  // State
  const [filter, setFilter] = useState<FilterType>('current');
  const [newGoal, setNewGoal] = useState('');
  const [newGoalStartDate, setNewGoalStartDate] = useState(() => {
    const today = getTodayDateInputValue();
    console.log('Initial date value:', today);
    return today;
  });
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [goalToDelete, setGoalToDelete] = useState<{ id: number; name: string } | null>(null);

  // Hooks
  const { data: goals = [], isLoading, error } = useGoals();
  const addGoalMutation = useAddGoal();
  const updateGoalMutation = useUpdateGoal();
  const deleteGoalMutation = useDeleteGoal();

  // Filtered goals
  const filteredGoals = useMemo(() => {
    if (filter === 'current') {
      return goals.filter(g => !g.end_date);
    }
    if (filter === 'past') {
      return goals.filter(g => g.end_date !== null);
    }
    return goals;
  }, [goals, filter]);

  // Handlers
  const handleAddGoal = async () => {
    const trimmedGoal = newGoal.trim();
    if (!trimmedGoal) return;

    // Check for duplicates (case-insensitive)
    const isDuplicate = goals.some(
      g => g.goal.toLowerCase() === trimmedGoal.toLowerCase() && !g.end_date
    );

    if (isDuplicate) {
      setDuplicateError(`"${trimmedGoal}" already exists as an active goal`);
      return;
    }

    try {
      await addGoalMutation.mutateAsync({
        goal: trimmedGoal,
        start_date: dateInputToISO(newGoalStartDate),
      });
      setNewGoal('');
      setNewGoalStartDate(getTodayDateInputValue());
      setDuplicateError(null);
    } catch (error) {
      console.error('Failed to add goal:', error);
    }
  };

  const handleEndGoal = async (goalId: number) => {
    try {
      await updateGoalMutation.mutateAsync({
        id: goalId,
        end_date: getCurrentTimestamp(),
      });
    } catch (error) {
      console.error('Failed to end goal:', error);
    }
  };

  const handleReactivateGoal = async (goalId: number) => {
    try {
      await updateGoalMutation.mutateAsync({
        id: goalId,
        end_date: null,
      });
    } catch (error) {
      console.error('Failed to reactivate goal:', error);
    }
  };

  const openDeleteModal = (goalId: number, goalName: string) => {
    setGoalToDelete({ id: goalId, name: goalName });
    setDeleteModalOpen(true);
  };

  const closeDeleteModal = () => {
    setDeleteModalOpen(false);
    setGoalToDelete(null);
  };

  const handleDeleteGoal = async () => {
    if (!goalToDelete) return;

    try {
      await deleteGoalMutation.mutateAsync(goalToDelete.id);
      closeDeleteModal();
    } catch (error) {
      console.error('Failed to delete goal:', error);
    }
  };

  return (
    <>
      {/* Header */}
      <header className="flex h-16 items-center border-b border-border bg-card px-6">
        <h1 className="text-xl font-semibold text-foreground">Goals</h1>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-4xl space-y-6">

          {/* Add Goal Section */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 text-sm font-medium text-foreground">Add New Goal</h2>
            <div className="space-y-3">
              <input
                type="text"
                value={newGoal}
                onChange={(e) => {
                  setNewGoal(e.target.value);
                  setDuplicateError(null);
                }}
                onKeyDown={(e) => e.key === 'Enter' && handleAddGoal()}
                placeholder="Enter a goal"
                className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type="date"
                    value={newGoalStartDate}
                    onChange={(e) => setNewGoalStartDate(e.target.value)}
                    className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    style={{ colorScheme: 'dark light' }}
                  />
                </div>
                <button
                  onClick={handleAddGoal}
                  disabled={!newGoal.trim() || addGoalMutation.isPending}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {addGoalMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
            {duplicateError && (
              <p className="mt-2 text-xs text-destructive">{duplicateError}</p>
            )}
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-2 border-b border-border">
            <button
              onClick={() => setFilter('current')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                filter === 'current'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Current
            </button>
            <button
              onClick={() => setFilter('past')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                filter === 'past'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Past
            </button>
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                filter === 'all'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All
            </button>
          </div>

          {/* Goals List */}
          {isLoading && (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
              Failed to load goals. Please try again.
            </div>
          )}

          {!isLoading && !error && filteredGoals.length === 0 && (
            <div className="py-12 text-center text-sm text-muted-foreground">
              {filter === 'current' && 'No active goals. Add one to get started!'}
              {filter === 'past' && 'No completed goals yet.'}
              {filter === 'all' && 'No goals yet. Add one to get started!'}
            </div>
          )}

          {!isLoading && !error && filteredGoals.length > 0 && (
            <div className="space-y-3">
              {filteredGoals.map((goal) => (
                <div
                  key={goal.id}
                  className="flex items-start justify-between rounded-lg border border-border bg-card p-4"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{goal.goal}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Started: {formatDate(goal.start_date)}
                      {goal.end_date && (
                        <span className="ml-2">
                          • Ended: {formatDate(goal.end_date)}
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {!goal.end_date && (
                      <Tooltip content="Mark goal as completed" position="top">
                        <button
                          onClick={() => handleEndGoal(goal.id)}
                          disabled={updateGoalMutation.isPending}
                          className="rounded p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                        </button>
                      </Tooltip>
                    )}
                    {goal.end_date && (
                      <Tooltip content="Reactivate goal" position="top">
                        <button
                          onClick={() => handleReactivateGoal(goal.id)}
                          disabled={updateGoalMutation.isPending}
                          className="rounded p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                      </Tooltip>
                    )}
                    <button
                      onClick={() => openDeleteModal(goal.id, goal.goal)}
                      disabled={deleteGoalMutation.isPending}
                      className="rounded p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive disabled:opacity-50"
                      title="Delete goal"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={closeDeleteModal}
        title="Delete Goal"
        size="sm"
        closeOnBackdrop={false}
        closeOnEscape={true}
      >
        <div className="space-y-4">
          <p className="text-sm text-foreground">
            Are you sure you want to delete <strong>"{goalToDelete?.name}"</strong>?
          </p>
          <p className="text-sm text-muted-foreground">
            This action cannot be undone.
          </p>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={closeDeleteModal}
              disabled={deleteGoalMutation.isPending}
              className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleDeleteGoal}
              disabled={deleteGoalMutation.isPending}
              className="flex-1 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleteGoalMutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Deleting...
                </span>
              ) : (
                'Delete'
              )}
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
