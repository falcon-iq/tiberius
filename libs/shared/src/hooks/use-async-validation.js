import { useCallback, useEffect, useRef, useState } from 'react';
import { getLogger } from '@libs/shared/utils/logger';
const logger = getLogger({ name: 'use-async-validation' });
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
export function useAsyncValidation({ validator, gate, extractErrorMessage, fallbackErrorMessage = 'Validation failed. Please try again.', debounceMs = 0, onSuccess, onError, }) {
    const [isValidating, setIsValidating] = useState(false);
    const [validationError, setValidationError] = useState('');
    const [isValid, setIsValid] = useState(false);
    // Last value successfully *scheduled/validated* to avoid repeated work on identical input.
    const lastValidatedValueRef = useRef('');
    // Request id for stale-response protection.
    const requestIdRef = useRef(0);
    // Abort controller for cancelling in-flight validation.
    const abortRef = useRef(null);
    // Debounce timer.
    const timerRef = useRef(null);
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
    const applyFailure = (msg) => {
        setIsValid(false);
        setValidationError(msg);
        onError?.(msg);
    };
    const applySuccess = (result) => {
        setIsValid(true);
        setValidationError('');
        onSuccess?.(result);
    };
    const validateNow = useCallback(async (raw) => {
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
        if (abortRef.current)
            abortRef.current.abort();
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
            if (myRequestId !== requestIdRef.current)
                return;
            if (result.valid) {
                applySuccess(result);
            }
            else {
                const msg = extractErrorMessage
                    ? (extractErrorMessage(result) ?? fallbackErrorMessage)
                    : (result.error ?? fallbackErrorMessage);
                applyFailure(msg);
            }
        }
        catch (err) {
            // Ignore stale result
            if (myRequestId !== requestIdRef.current)
                return;
            // Abort is not an error for UX; do not overwrite state.
            if (controller.signal.aborted) {
                return;
            }
            logger.error(err, 'Validation failed with exception');
            // Allow retry of the same value after a real error
            lastValidatedValueRef.current = '';
            applyFailure(fallbackErrorMessage);
        }
        finally {
            // Only clear validating if this is still the latest request
            if (myRequestId === requestIdRef.current) {
                setIsValidating(false);
                abortRef.current = null;
            }
        }
    }, [
        applyFailure,
        applySuccess,
        cancel,
        extractErrorMessage,
        fallbackErrorMessage,
        gate,
        validator,
    ]);
    const validate = useCallback((value) => {
        // If no debounce, validate immediately (but still async).
        if (!debounceMs || debounceMs <= 0) {
            void validateNow(value);
            return;
        }
        clearTimer();
        timerRef.current = setTimeout(() => {
            void validateNow(value);
        }, debounceMs);
    }, [debounceMs, validateNow]);
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
