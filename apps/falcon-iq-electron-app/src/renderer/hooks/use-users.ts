import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AddUserInput } from '@generatedtypes/electron';

const USERS_QUERY_KEY = ['users'];

/**
 * Hook to fetch all users from SQLite database
 */
export function useUsers() {
  return useQuery({
    queryKey: USERS_QUERY_KEY,
    queryFn: async () => {
      const result = await window.api.getUsers();
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch users');
      }
      return result.data || [];
    },
  });
}

/**
 * Hook to add a new user to the database
 */
export function useAddUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (user: AddUserInput) => {
      const result = await window.api.addUser(user);
      if (!result.success) {
        throw new Error(result.error || 'Failed to add user');
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate and refetch users query
      void queryClient.invalidateQueries({ queryKey: USERS_QUERY_KEY });
    },
  });
}

/**
 * Hook to delete a user from the database
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const result = await window.api.deleteUser(id);
      if (!result.success) {
        throw new Error(result.error || 'Failed to delete user');
      }
    },
    onSuccess: () => {
      // Invalidate and refetch users query
      void queryClient.invalidateQueries({ queryKey: USERS_QUERY_KEY });
    },
  });
}
