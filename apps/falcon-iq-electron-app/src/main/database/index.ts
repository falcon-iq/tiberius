// Database initialization
export { initDatabase, closeDatabase } from './init';

// User operations
export { getUsers, addUser, deleteUser } from './users';
export type { User, AddUserInput } from './users';

// Goal operations
export { getGoals, addGoal, deleteGoal, updateGoal } from './goals';
export type { Goal, AddGoalInput, UpdateGoalInput } from './goals';

// PR comment statistics
export { getPRCommentStats, getPRCommentsByMetric } from './pr-comment-details';
export type {
  PRCommentRow,
  PRCommentStats,
  CategoryStat,
  SeverityStat
} from './pr-comment-details';
