import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query'
import { ApiError } from '@types/index'
import { useUIStore } from '@store/index'
import { NotificationType } from '@types/index'

// Custom hook for API queries with error handling
export function useApiQuery<TData = unknown>(
  queryKey: any[],
  queryFn: () => Promise<TData>,
  options?: Omit<UseQueryOptions<TData, ApiError>, 'queryKey' | 'queryFn'>,
) {
  const addNotification = useUIStore((state) => state.addNotification)

  return useQuery<TData, ApiError>({
    queryKey,
    queryFn,
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error.status >= 400 && error.status < 500) {
        return false
      }
      return failureCount < 3
    },
    ...options,
    onError: (error) => {
      addNotification({
        type: NotificationType.ERROR,
        title: 'Error',
        message: error.message || 'An error occurred while fetching data',
      })
      options?.onError?.(error)
    },
  })
}

// Custom hook for API mutations with optimistic updates
export function useApiMutation<TData = unknown, TVariables = unknown>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseMutationOptions<TData, ApiError, TVariables>,
) {
  const queryClient = useQueryClient()
  const addNotification = useUIStore((state) => state.addNotification)

  return useMutation<TData, ApiError, TVariables>({
    mutationFn,
    ...options,
    onSuccess: (data, variables, context) => {
      addNotification({
        type: NotificationType.SUCCESS,
        title: 'Success',
        message: 'Operation completed successfully',
      })
      options?.onSuccess?.(data, variables, context)
    },
    onError: (error, variables, context) => {
      addNotification({
        type: NotificationType.ERROR,
        title: 'Error',
        message: error.message || 'An error occurred',
      })
      options?.onError?.(error, variables, context)
    },
  })
}