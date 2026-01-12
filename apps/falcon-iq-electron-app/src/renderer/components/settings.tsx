import { useNavigate } from '@tanstack/react-router';
import { useEffect, useState } from "react";
import { Modal } from "@libs/shared/ui";

export const Settings = () => {
  const navigate = useNavigate();
  const [pat, setPat] = useState("");

  useEffect(() => {
    setPat(localStorage.getItem("manager_buddy_pat") ?? "");
  }, []);

  const handleClose = () => {
    navigate({ to: '/' });
  };

  const handleSave = () => {
    localStorage.setItem("manager_buddy_pat", pat);
    handleClose();
  };

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title="Settings"
      size="md"
      initialFocusId="pat"
    >
      <div className="space-y-4">
        <div>
          <label
            htmlFor="pat"
            className="mb-2 block text-sm font-medium text-foreground"
          >
            Personal Access Token
          </label>
          <input
            id="pat"
            type="password"
            value={pat}
            onChange={(e) => setPat(e.target.value)}
            placeholder="Enter your PAT"
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <p className="mt-2 text-xs text-muted-foreground">
            Your PAT will be stored and used to authenticate with your project management tools.
          </p>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            onClick={handleClose}
            className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
            type="button"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            type="button"
          >
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
}
