import { useState, useRef, useEffect } from 'react';
import { getLogger } from '@libs/shared/utils';

const logger = getLogger({ name: 'use-async-validation' });

export interface ValidationResult {
    valid: boolean;
    error?: string;
}

export interface UseAsyncValidationOptions<T> {
    /**
     * The async validator function that takes a value and returns a validation result.
     */
    validator: (value: string) => Promise<T>;

    /**
     * Extracts the error message from the validation result when validation fails.
     * If not provided, will use result.error if it exists.
     */
    extractErrorMessage?: (result: T) => string | undefined;

    /**
     * Fallback error message to display when the validator throws an exception.
     * Default: "Validation failed. Please try again."
     */
    fallbackErrorMessage?: string;

    /**
     * Optional callback invoked when validation succeeds.
     */
    onSuccess?: (result: T) => void;

    /**
     * Optional callback invoked when validation fails or throws an error.
     */
    onError?: (error: string) => void;
}

export interface UseAsyncValidationReturn {
    /**
     * Function to trigger validation. Should typically be called on blur or debounced input.
     */
    validate: (value: string) => Promise<void>;

    /**
     * True while validation is in progress.
     */
    isValidating: boolean;

    /**
     * Error message if validation failed, empty string otherwise.
     */
    validationError: string;

    /**
     * True if the last validation succeeded.
     */
    isValid: boolean;

    /**
     * Resets all validation state to initial values.
     */
    reset: () => void;
}

/**
 * A custom hook for handling async validation with built-in guards against:
 * - Re-entrancy (prevents multiple simultaneous validations)
 * - Value deduplication (prevents validating the same value repeatedly)
 * - Proper cleanup on unmount
 *
 * @example
 * ```tsx
 * const { validate, isValidating, validationError, isValid } = useAsyncValidation({
 *   validator: validateGitHubToken,
 *   extractErrorMessage: (result) => result.error || "Invalid token",
 *   fallbackErrorMessage: "Failed to validate. Please check your connection."
 * });
 *
 * return (
 *   <input
 *     onBlur={(e) => validate(e.target.value)}
 *     className={validationError ? "border-red" : "border-gray"}
 *   />
 * );
 * ```
 */
export function useAsyncValidation<T extends ValidationResult>({
    validator,
    extractErrorMessage,
    fallbackErrorMessage = 'Validation failed. Please try again.',
    onSuccess,
    onError,
}: UseAsyncValidationOptions<T>): UseAsyncValidationReturn {
    const [isValidating, setIsValidating] = useState(false);
    const [validationError, setValidationError] = useState<string>('');
    const [isValid, setIsValid] = useState(false);

    // Track the last value we validated to avoid validating the same value repeatedly
    const lastValidatedRef = useRef<string>('');

    // Debounce timer to avoid blur/focus churn triggering back-to-back validations
    const validateTimerRef = useRef<number | null>(null);

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (validateTimerRef.current) {
                clearTimeout(validateTimerRef.current);
                validateTimerRef.current = null;
            }
        };
    }, []);

    const validate = async (raw: string): Promise<void> => {
        const v = raw.trim();

        // Empty value resets validation state
        if (!v) {
            setValidationError('');
            setIsValid(false);
            return;
        }

        // Prevent re-entrancy during focus/blur churn
        if (isValidating) {
            return;
        }

        // Prevent validating the same value repeatedly
        if (v === lastValidatedRef.current) {
            return;
        }

        // Mark as last validated up front to suppress loops
        lastValidatedRef.current = v;

        setIsValidating(true);
        setValidationError('');

        try {
            const result = await validator(v);

            if (result.valid) {
                setIsValid(true);
                setValidationError('');
                onSuccess?.(result);
            } else {
                setIsValid(false);
                const errorMsg = extractErrorMessage
                    ? (extractErrorMessage(result) ?? fallbackErrorMessage)
                    : (result.error ?? fallbackErrorMessage);
                setValidationError(errorMsg);
                onError?.(errorMsg);
            }
        } catch (err) {
            logger.error(err, 'Validation failed with exception');
            // Reset last validated so user can retry the same value
            lastValidatedRef.current = '';
            setIsValid(false);
            setValidationError(fallbackErrorMessage);
            onError?.(fallbackErrorMessage);
        } finally {
            setIsValidating(false);
        }
    };

    const reset = () => {
        setIsValidating(false);
        setValidationError('');
        setIsValid(false);
        lastValidatedRef.current = '';
    };

    return {
        validate,
        isValidating,
        validationError,
        isValid,
        reset,
    };
}
