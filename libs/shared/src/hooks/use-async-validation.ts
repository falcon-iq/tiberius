import { useCallback, useEffect, useRef, useState } from 'react';
import { getLogger } from '../utils/logger';

const logger = getLogger({ name: 'use-async-validation' });

export interface ValidationResult {
    valid: boolean;
    error?: string;
}

/**
 * If your validator supports AbortController, accept `signal` and stop work on abort.
 * If it doesn't, you can ignore `signal`; we will still prevent stale results from applying.
 */
export type AsyncValidator<T> = (value: string, ctx: { signal: AbortSignal }) => Promise<T>;

export interface UseAsyncValidationOptions<T> {
    /**
     * Async validator. Strongly recommended to honor ctx.signal for fetch/XHR cancellation.
     */
    validator: AsyncValidator<T>;

    /**
     * Optional cheap synchronous gate. If it returns an error string, async validation is skipped.
     * Example: regex/prefix checks, min length, etc.
     */
    gate?: (value: string) => string | undefined;

    /**
     * Extract error message from a failed validation result.
     * If not provided, will use result.error if it exists.
     */
    extractErrorMessage?: (result: T) => string | undefined;

    /**
     * Fallback error message when validator throws (non-abort) or provides no error detail.
     */
    fallbackErrorMessage?: string;

    /**
     * Optional debounce (ms). 0/undefined disables debouncing.
     * Typical values: 250–500ms for onChange validation; 0 for onBlur.
     */
    debounceMs?: number;

    /**
     * Optional callback invoked when validation succeeds (non-stale result).
     */
    onSuccess?: (result: T) => void;

    /**
     * Optional callback invoked when validation fails (non-stale result).
     */
    onError?: (error: string) => void;
}

export interface UseAsyncValidationReturn {
    /**
     * Trigger validation for the provided value.
     * Safe against re-entrancy, supports dedupe, debounce, and stale-result protection.
     */
    validate: (value: string) => void;

    /**
     * Immediately validate, bypassing debounce (useful for onBlur or submit-time checks).
     */
    validateNow: (value: string) => Promise<void>;

    /**
     * Cancel any in-flight validation and pending debounce timer.
     */
    cancel: () => void;

    /**
     * True while the latest request is in-flight.
     */
    isValidating: boolean;

    /**
     * Error message if validation failed, empty string otherwise.
     * (Note: if you use RHF, you may choose to ignore this and push errors via setError instead.)
     */
    validationError: string;

    /**
     * True if the last *applied* validation succeeded.
     */
    isValid: boolean;

    /**
     * Resets all validation state (and cancels any pending/in-flight work).
     */
    reset: () => void;
}

/**
 * Async validation hook with:
 * - Optional sync gating (avoid XHR if format is obviously wrong)
 * - Debounce (optional)
 * - Cancellation via AbortController (recommended)
 * - Stale response protection (request id)
 * - Value deduplication (skip validating same value repeatedly)
 *
 * Usage example (onBlur):
 *   const { validateNow, isValidating, validationError } = useAsyncValidation({...});
 *   <input onBlur={(e) => validateNow(e.target.value)} />
 *
 * Usage example (onChange w/ debounce):
 *   const { validate } = useAsyncValidation({ debounceMs: 400, ... });
 *   <input onChange={(e) => validate(e.target.value)} />
 */
export function useAsyncValidation<T extends ValidationResult>({
    validator,
    gate,
    extractErrorMessage,
    fallbackErrorMessage = 'Validation failed. Please try again.',
    debounceMs = 0,
    onSuccess,
    onError,
}: UseAsyncValidationOptions<T>): UseAsyncValidationReturn {
    const [isValidating, setIsValidating] = useState(false);
    const [validationError, setValidationError] = useState<string>('');
    const [isValid, setIsValid] = useState(false);

    // Last value successfully *scheduled/validated* to avoid repeated work on identical input.
    const lastValidatedValueRef = useRef<string>('');

    // Request id for stale-response protection.
    const requestIdRef = useRef(0);

    // Abort controller for cancelling in-flight validation.
    const abortRef = useRef<AbortController | null>(null);

    // Debounce timer.
    const timerRef = useRef<number | null>(null);

    const clearTimer = () => {
        if (timerRef.current !== null) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
    };

    const cancel = useCallback(() => {
        clearTimer();
        if (abortRef.current) {
            abortRef.current.abort();
            abortRef.current = null;
        }
        setIsValidating(false);
    }, []);

    useEffect(() => {
        return () => {
            // Cleanup on unmount
            cancel();
        };
    }, [cancel]);

    const applyFailure = (msg: string) => {
        setIsValid(false);
        setValidationError(msg);
        onError?.(msg);
    };

    const applySuccess = (result: T) => {
        setIsValid(true);
        setValidationError('');
        onSuccess?.(result);
    };

    const validateNow = useCallback(
        async (raw: string): Promise<void> => {
            const v = raw.trim();

            // Empty value resets state (treat as "not validated").
            if (!v) {
                cancel();
                lastValidatedValueRef.current = '';
                setIsValid(false);
                setValidationError('');
                return;
            }

            // Value dedupe
            if (v === lastValidatedValueRef.current) {
                return;
            }

            // Optional sync gate (format, length, etc.)
            const gateError = gate?.(v);
            if (gateError) {
                cancel(); // cancel any in-flight since the current value is gated
                lastValidatedValueRef.current = v;
                applyFailure(gateError);
                return;
            }

            // Cancel any in-flight request + bump request id for stale-result protection
            clearTimer();
            if (abortRef.current) abortRef.current.abort();
            const controller = new AbortController();
            abortRef.current = controller;

            const myRequestId = ++requestIdRef.current;

            // Record value up front to suppress loops; if request fails non-abort, we'll allow retry.
            lastValidatedValueRef.current = v;

            setIsValidating(true);
            setValidationError('');

            try {
                const result = await validator(v, { signal: controller.signal });

                // Ignore stale result
                if (myRequestId !== requestIdRef.current) return;

                if (result.valid) {
                    applySuccess(result);
                } else {
                    const msg = extractErrorMessage
                        ? (extractErrorMessage(result) ?? fallbackErrorMessage)
                        : (result.error ?? fallbackErrorMessage);
                    applyFailure(msg);
                }
            } catch (err: any) {
                // Ignore stale result
                if (myRequestId !== requestIdRef.current) return;

                // Abort is not an error for UX; do not overwrite state.
                if (controller.signal.aborted) {
                    return;
                }

                logger.error(err, 'Validation failed with exception');

                // Allow retry of the same value after a real error
                lastValidatedValueRef.current = '';

                applyFailure(fallbackErrorMessage);
            } finally {
                // Only clear validating if this is still the latest request
                if (myRequestId === requestIdRef.current) {
                    setIsValidating(false);
                    abortRef.current = null;
                }
            }
        },
        [
            applyFailure,
            applySuccess,
            cancel,
            extractErrorMessage,
            fallbackErrorMessage,
            gate,
            validator,
        ],
    );

    const validate = useCallback(
        (value: string) => {
            // If no debounce, validate immediately (but still async).
            if (!debounceMs || debounceMs <= 0) {
                void validateNow(value);
                return;
            }

            clearTimer();
            timerRef.current = setTimeout(() => {
                void validateNow(value);
            }, debounceMs) as unknown as number;
        },
        [debounceMs, validateNow],
    );

    const reset = useCallback(() => {
        cancel();
        requestIdRef.current += 1; // invalidate any pending completions
        lastValidatedValueRef.current = '';
        setIsValid(false);
        setValidationError('');
    }, [cancel]);

    return {
        validate,
        validateNow,
        cancel,
        isValidating,
        validationError,
        isValid,
        reset,
    };
}
