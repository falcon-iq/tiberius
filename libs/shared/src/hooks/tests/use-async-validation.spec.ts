import { renderHook, waitFor, act } from '@testing-library/react';
import { useAsyncValidation, type ValidationResult } from '../use-async-validation';

describe('useAsyncValidation', () => {
  const mockSuccessValidator = jest.fn(async (value: string, ctx: { signal: AbortSignal }): Promise<ValidationResult> => {
    return { valid: true };
  });

  const mockFailureValidator = jest.fn(async (value: string, ctx: { signal: AbortSignal }): Promise<ValidationResult> => {
    return { valid: false, error: 'Invalid value' };
  });

  const mockThrowingValidator = jest.fn(async (value: string, ctx: { signal: AbortSignal }): Promise<ValidationResult> => {
    throw new Error('Network error');
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('basic validation', () => {
    it('should validate successfully', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      expect(result.current.isValid).toBe(false);
      expect(result.current.isValidating).toBe(false);

      await act(async () => {
        await result.current.validate('test-value');
      });

      await waitFor(() => {
        expect(result.current.isValid).toBe(true);
        expect(result.current.validationError).toBe('');
      });

      expect(mockSuccessValidator).toHaveBeenCalledWith('test-value', expect.objectContaining({ signal: expect.any(AbortSignal) }));
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);
    });

    it('should handle validation failure', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockFailureValidator,
        })
      );

      await act(async () => {
        await result.current.validate('bad-value');
      });

      await waitFor(() => {
        expect(result.current.isValid).toBe(false);
        expect(result.current.validationError).toBe('Invalid value');
      });

      expect(mockFailureValidator).toHaveBeenCalledWith('bad-value', expect.objectContaining({ signal: expect.any(AbortSignal) }));
    });

    it('should handle exceptions with fallback message', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockThrowingValidator,
          fallbackErrorMessage: 'Connection failed',
        })
      );

      await act(async () => {
        await result.current.validate('test-value');
      });

      await waitFor(() => {
        expect(result.current.isValid).toBe(false);
        expect(result.current.validationError).toBe('Connection failed');
      });
    });
  });

  describe('empty value handling', () => {
    it('should reset state when validating empty string', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      // First validate a value
      await act(async () => {
        await result.current.validate('test-value');
      });
      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Then validate empty string
      await act(async () => {
        await result.current.validate('');
      });

      await waitFor(() => {
        expect(result.current.isValid).toBe(false);
        expect(result.current.validationError).toBe('');
        expect(result.current.isValidating).toBe(false);
      });
    });

    it('should trim whitespace', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      await act(async () => {
        await result.current.validate('  test-value  ');
      });

      await waitFor(() => {
        expect(result.current.isValid).toBe(true);
      });

      expect(mockSuccessValidator).toHaveBeenCalledWith('test-value', expect.objectContaining({ signal: expect.any(AbortSignal) }));
    });
  });

  describe('deduplication', () => {
    it('should not validate the same value twice', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      await act(async () => {
        await result.current.validate('test-value');
      });
      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Try to validate the same value again
      await act(async () => {
        await result.current.validate('test-value');
      });

      // Should still only be called once
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);
    });

    it('should validate different values', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      await act(async () => {
        await result.current.validate('value1');
      });
      await waitFor(() => expect(result.current.isValid).toBe(true));

      await act(async () => {
        await result.current.validate('value2');
      });
      await waitFor(() => expect(mockSuccessValidator).toHaveBeenCalledTimes(2));

      expect(mockSuccessValidator).toHaveBeenNthCalledWith(1, 'value1', expect.objectContaining({ signal: expect.any(AbortSignal) }));
      expect(mockSuccessValidator).toHaveBeenNthCalledWith(2, 'value2', expect.objectContaining({ signal: expect.any(AbortSignal) }));
    });
  });

  describe('re-entrancy protection', () => {
    it('should cancel previous validation when new one starts', async () => {
      const slowValidator = jest.fn(
        async (value: string, ctx: { signal: AbortSignal }): Promise<ValidationResult> => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          // Check if aborted during the delay
          if (ctx.signal.aborted) {
            throw new Error('Aborted');
          }
          return { valid: true };
        }
      );

      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: slowValidator,
        })
      );

      // Start first validation
      await act(async () => {
        void result.current.validate('value1');
      });

      // Immediately try second validation while first is still running
      // This should abort the first and start the second
      await act(async () => {
        await result.current.validate('value2');
      });

      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Both will be called, but the first will be aborted
      expect(slowValidator).toHaveBeenCalledTimes(2);
      expect(slowValidator).toHaveBeenNthCalledWith(1, 'value1', expect.objectContaining({ signal: expect.any(AbortSignal) }));
      expect(slowValidator).toHaveBeenNthCalledWith(2, 'value2', expect.objectContaining({ signal: expect.any(AbortSignal) }));
    });
  });

  describe('callbacks', () => {
    it('should call onSuccess callback', async () => {
      const onSuccess = jest.fn();
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
          onSuccess,
        })
      );

      await act(async () => {
        await result.current.validate('test-value');
      });

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith({ valid: true });
      });
    });

    it('should call onError callback on validation failure', async () => {
      const onError = jest.fn();
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockFailureValidator,
          onError,
        })
      );

      await act(async () => {
        await result.current.validate('bad-value');
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Invalid value');
      });
    });

    it('should call onError callback on exception', async () => {
      const onError = jest.fn();
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockThrowingValidator,
          fallbackErrorMessage: 'Connection failed',
          onError,
        })
      );

      await act(async () => {
        await result.current.validate('test-value');
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Connection failed');
      });
    });
  });

  describe('custom error message extraction', () => {
    it('should use extractErrorMessage function', async () => {
      interface CustomValidationResult extends ValidationResult {
        details?: string;
      }

      const customValidator = jest.fn(async (): Promise<CustomValidationResult> => {
        return { valid: false, error: 'ERR_001', details: 'Detailed error message' };
      });

      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: customValidator,
          extractErrorMessage: (result: CustomValidationResult) => result.details || result.error,
        })
      );

      await act(async () => {
        await result.current.validate('test-value');
      });

      await waitFor(() => {
        expect(result.current.validationError).toBe('Detailed error message');
      });
    });
  });

  describe('reset functionality', () => {
    it('should reset all state', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      // Validate a value
      await act(async () => {
        await result.current.validate('test-value');
      });
      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Reset
      act(() => {
        result.current.reset();
      });

      await waitFor(() => {
        expect(result.current.isValid).toBe(false);
        expect(result.current.validationError).toBe('');
        expect(result.current.isValidating).toBe(false);
      });
    });

    it('should allow re-validating same value after reset', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      // First validation
      await act(async () => {
        await result.current.validate('test-value');
      });
      await waitFor(() => expect(result.current.isValid).toBe(true));
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);

      // Try to validate same value again (should be skipped)
      await act(async () => {
        await result.current.validate('test-value');
      });
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);

      // Reset and validate again
      act(() => {
        result.current.reset();
      });
      await act(async () => {
        await result.current.validate('test-value');
      });
      await waitFor(() => expect(mockSuccessValidator).toHaveBeenCalledTimes(2));
    });
  });
});
