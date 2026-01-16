import { renderHook, waitFor } from '@testing-library/react';
import { useAsyncValidation, type ValidationResult } from '../use-async-validation';

describe('useAsyncValidation', () => {
  const mockSuccessValidator = jest.fn(async (value: string): Promise<ValidationResult> => {
    return { valid: true };
  });

  const mockFailureValidator = jest.fn(async (value: string): Promise<ValidationResult> => {
    return { valid: false, error: 'Invalid value' };
  });

  const mockThrowingValidator = jest.fn(async (value: string): Promise<ValidationResult> => {
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

      await result.current.validate('test-value');

      await waitFor(() => {
        expect(result.current.isValid).toBe(true);
        expect(result.current.validationError).toBe('');
      });

      expect(mockSuccessValidator).toHaveBeenCalledWith('test-value');
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);
    });

    it('should handle validation failure', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockFailureValidator,
        })
      );

      await result.current.validate('bad-value');

      await waitFor(() => {
        expect(result.current.isValid).toBe(false);
        expect(result.current.validationError).toBe('Invalid value');
      });

      expect(mockFailureValidator).toHaveBeenCalledWith('bad-value');
    });

    it('should handle exceptions with fallback message', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockThrowingValidator,
          fallbackErrorMessage: 'Connection failed',
        })
      );

      await result.current.validate('test-value');

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
      await result.current.validate('test-value');
      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Then validate empty string
      await result.current.validate('');

      expect(result.current.isValid).toBe(false);
      expect(result.current.validationError).toBe('');
      expect(result.current.isValidating).toBe(false);
    });

    it('should trim whitespace', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      await result.current.validate('  test-value  ');

      await waitFor(() => {
        expect(result.current.isValid).toBe(true);
      });

      expect(mockSuccessValidator).toHaveBeenCalledWith('test-value');
    });
  });

  describe('deduplication', () => {
    it('should not validate the same value twice', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      await result.current.validate('test-value');
      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Try to validate the same value again
      await result.current.validate('test-value');

      // Should still only be called once
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);
    });

    it('should validate different values', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      await result.current.validate('value1');
      await waitFor(() => expect(result.current.isValid).toBe(true));

      await result.current.validate('value2');
      await waitFor(() => expect(mockSuccessValidator).toHaveBeenCalledTimes(2));

      expect(mockSuccessValidator).toHaveBeenNthCalledWith(1, 'value1');
      expect(mockSuccessValidator).toHaveBeenNthCalledWith(2, 'value2');
    });
  });

  describe('re-entrancy protection', () => {
    it('should prevent concurrent validations', async () => {
      const slowValidator = jest.fn(
        async (value: string): Promise<ValidationResult> => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return { valid: true };
        }
      );

      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: slowValidator,
        })
      );

      // Start first validation
      void result.current.validate('value1');

      // Immediately try second validation while first is still running
      await result.current.validate('value2');

      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Should only have been called once
      expect(slowValidator).toHaveBeenCalledTimes(1);
      expect(slowValidator).toHaveBeenCalledWith('value1');
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

      await result.current.validate('test-value');

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

      await result.current.validate('bad-value');

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

      await result.current.validate('test-value');

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

      await result.current.validate('test-value');

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
      await result.current.validate('test-value');
      await waitFor(() => expect(result.current.isValid).toBe(true));

      // Reset
      result.current.reset();

      expect(result.current.isValid).toBe(false);
      expect(result.current.validationError).toBe('');
      expect(result.current.isValidating).toBe(false);
    });

    it('should allow re-validating same value after reset', async () => {
      const { result } = renderHook(() =>
        useAsyncValidation({
          validator: mockSuccessValidator,
        })
      );

      // First validation
      await result.current.validate('test-value');
      await waitFor(() => expect(result.current.isValid).toBe(true));
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);

      // Try to validate same value again (should be skipped)
      await result.current.validate('test-value');
      expect(mockSuccessValidator).toHaveBeenCalledTimes(1);

      // Reset and validate again
      result.current.reset();
      await result.current.validate('test-value');
      await waitFor(() => expect(mockSuccessValidator).toHaveBeenCalledTimes(2));
    });
  });
});
