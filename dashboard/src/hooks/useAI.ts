import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/api/client';

export const aiQueryKeys = {
  config: ['aiConfig'] as const,
  operations: ['aiOperations'] as const,
  models: ['aiModels'] as const,
  backends: ['aiBackends'] as const,
  tasks: ['aiTasks'] as const,
  task: (id: string) => ['aiTask', id] as const,
  queueStats: ['aiQueueStats'] as const,
};

export const useAIConfig = () =>
  useQuery({
    queryKey: aiQueryKeys.config,
    queryFn: api.getAIConfig,
    staleTime: 60000, // 1 minute
  });

export const useUpdateAIConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.updateAIConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiQueryKeys.config });
    },
  });
};

export const useAIOperations = () =>
  useQuery({
    queryKey: aiQueryKeys.operations,
    queryFn: api.getAIOperations,
    staleTime: 300000, // 5 minutes - these don't change
  });

export const useAIModels = () =>
  useQuery({
    queryKey: aiQueryKeys.models,
    queryFn: api.getAIModels,
    staleTime: 300000,
  });

export const useAIBackends = () =>
  useQuery({
    queryKey: aiQueryKeys.backends,
    queryFn: api.getAIBackends,
    staleTime: 300000,
  });

export const useProcessAI = () => {
  return useMutation({
    mutationFn: api.processAI,
  });
};

// ===== Task Queue Hooks (Claude Code Integration) =====

export const useAITasks = (status?: string, refetchInterval?: number) => {
  return useQuery({
    queryKey: [...aiQueryKeys.tasks, status],
    queryFn: () => api.getAITasks(status),
    staleTime: 5000, // 5 seconds - tasks update frequently
    refetchInterval: refetchInterval || 5000, // Poll every 5 seconds by default
  });
};

export const useAITask = (taskId: string | null) => {
  return useQuery({
    queryKey: aiQueryKeys.task(taskId || ''),
    queryFn: () => api.getAITask(taskId!),
    enabled: !!taskId,
    staleTime: 2000,
    refetchInterval: 2000, // Poll while watching a specific task
  });
};

export const useSubmitAITask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.submitAITask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiQueryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: aiQueryKeys.queueStats });
    },
  });
};

export const useCancelAITask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.cancelAITask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiQueryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: aiQueryKeys.queueStats });
    },
  });
};

export const useAIQueueStats = () => {
  return useQuery({
    queryKey: aiQueryKeys.queueStats,
    queryFn: api.getAIQueueStats,
    staleTime: 10000,
    refetchInterval: 10000,
  });
};
