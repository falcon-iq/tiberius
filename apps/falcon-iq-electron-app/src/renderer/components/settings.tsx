import { useRouter } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Modal } from "@libs/shared/ui";
import { useForm } from "react-hook-form";
import { validateGitHubToken } from "@libs/integrations/github/auth";
import { Loader2 } from "lucide-react";
import { getLogger } from '@libs/shared/utils';

interface SettingsFormData {
  pat: string;
}

const logger = getLogger({ name: "settings" });

export const Settings = () => {
  const router = useRouter();
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState<string>("");
  const [isValid, setIsValid] = useState(false);

  const { register, handleSubmit, setValue } = useForm<SettingsFormData>({
    defaultValues: { pat: "" },
  });

  // Track the last value we validated to avoid validating the same token repeatedly
  const lastValidatedRef = useRef<string>("");

  // Debounce timer to avoid blur/focus churn triggering back-to-back validations
  const validateTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const storedPat = localStorage.getItem("manager_buddy_pat") ?? "";
    setValue("pat", storedPat);
  }, [setValue]);

  useEffect(() => {
    return () => {
      if (validateTimerRef.current) {
        window.clearTimeout(validateTimerRef.current);
        validateTimerRef.current = null;
      }
    };
  }, []);

  const handleClose = () => {
    router.history.back();
  };

  const validatePat = async (raw: string) => {
    const v = raw.trim();
    if (!v) {
      setValidationError("");
      setIsValid(false);
      return;
    }

    // Prevent re-entrancy during focus/blur churn
    if (isValidating) return;

    // Prevent validating the same value repeatedly
    if (v === lastValidatedRef.current) return;

    // Mark as last validated up front to suppress loops.
    lastValidatedRef.current = v;

    setIsValidating(true);
    setValidationError("");
    
    try {
      const result = await validateGitHubToken(v);
      
      if (result.valid) {
        setIsValid(true);
        setValidationError("");
      } else {
        setIsValid(false);
        setValidationError(result.error || "Invalid GitHub token");
      }
    } catch (err) {
      logger.error(err, "Failed to validate token");
      lastValidatedRef.current = "";
      setIsValid(false);
      setValidationError("Failed to validate token. Please check your connection.");
    } finally {
      setIsValidating(false);
    }
  };

  const onSubmit = (data: SettingsFormData) => {
    localStorage.setItem("manager_buddy_pat", data.pat);
    handleClose();
  };

  const patField = register("pat");

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title="Settings"
      size="md"
      initialFocusId="pat"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label
            htmlFor="pat"
            className="mb-2 block text-sm font-medium text-foreground"
          >
            Personal Access Token
          </label>

            <div className="relative">
              <input
                id="pat"
                type="password"
                {...patField}
                onBlur={(e) => {
                  patField.onBlur(e);
                  void validatePat(e.target.value);
                }}
                placeholder="Enter your PAT"
                className={`w-full rounded-lg border bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
                  validationError
                    ? "border-destructive focus:ring-destructive"
                    : "border-border focus:ring-primary"
                }`}
              />

              {isValidating && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              )}
            </div>

            <div className="mt-2 min-h-[20px]">
              {validationError ? (
                <p className="text-xs text-destructive">
                  {validationError}
                </p>
              ) : null}
            </div>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Cancel
          </button>

            <button
              type="submit"
              disabled={!isValid || isValidating}
              className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save
            </button>
        </div>
      </form>
    </Modal>
  );
};
