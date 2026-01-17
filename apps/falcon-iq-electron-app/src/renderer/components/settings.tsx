import { useRouter } from "@tanstack/react-router";
import { useEffect } from "react";
import { Modal } from "@libs/shared/ui/modal/modal";
import { useForm } from "react-hook-form";
import { validateGitHubToken, type ValidateTokenResult } from "@libs/integrations/github/auth";
import { Loader2 } from "lucide-react";
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';

interface SettingsFormData {
  pat: string;
  suffix: string;
}

export const Settings = () => {
  const router = useRouter();
  
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<SettingsFormData>({
    defaultValues: { pat: "", suffix: "" },
    mode: "onBlur", // Validate on blur instead of only on submit
  });

  // Use the async validation hook
  const { validate, isValidating, validationError, isValid } = useAsyncValidation({
    validator: validateGitHubToken,
    extractErrorMessage: (result: ValidateTokenResult) => result.error ?? "Invalid GitHub token",
    fallbackErrorMessage: "Failed to validate token. Please check your connection."
  });

  useEffect(() => {
    const storedPat = localStorage.getItem("manager_buddy_pat") ?? "";
    const storedSuffix = localStorage.getItem("manager_buddy_suffix") ?? "";
    setValue("pat", storedPat);
    setValue("suffix", storedSuffix);
  }, [setValue]);

  const handleClose = () => {
    router.history.back();
  };

  const onSubmit = (data: SettingsFormData) => {
    localStorage.setItem("manager_buddy_pat", data.pat);
    localStorage.setItem("manager_buddy_suffix", data.suffix);
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
                  void validate(e.target.value);
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

        <div>
          <label
            htmlFor="suffix"
            className="mb-2 block text-sm font-medium text-foreground"
          >
            Suffix
          </label>

          <input
            id="suffix"
            type="text"
            {...register("suffix", {
              required: "Suffix is required",
              validate: (value) => value.trim().length > 0 || "Suffix cannot be empty"
            })}
            placeholder="Enter suffix"
            className={`w-full rounded-lg border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
              errors.suffix
                ? "border-destructive focus:ring-destructive"
                : "border-border focus:ring-primary"
            }`}
          />

          <div className="mt-2 min-h-[20px]">
            {errors.suffix ? (
              <p className="text-xs text-destructive">
                {errors.suffix.message}
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
