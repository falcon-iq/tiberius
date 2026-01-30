/**
 * Shared types for onboarding wizard components
 */

/**
 * User details from Step 1
 */
export interface UserDetails {
  firstName: string;
  lastName: string;
  ldapUsername: string;
}

/**
 * GitHub integration details from Step 2
 */
export interface GitHubIntegration {
  pat: string;
  emuSuffix?: string;
  username?: string;
}

/**
 * Team member with GitHub profile data
 */
export interface TeamMember {
  username: string;
  firstname?: string;
  lastname?: string;
  email_address?: string;
  github_suffix?: string | null;
  avatar_url?: string;
}

/**
 * Goal with start and end dates
 */
export interface Goal {
  id: number;
  goal: string;
  start_date: string;
  end_date: string | null;
}

/**
 * Step component props
 */
export interface StepComponentProps {
  onNext: () => void;
  onBack?: () => void;
}

/**
 * Step 1 props
 */
export interface Step1Props extends StepComponentProps {
  userDetails: UserDetails;
  onDataChange: (data: UserDetails) => void;
}

/**
 * Step 2 props
 */
export interface Step2Props extends StepComponentProps {
  userDetails: UserDetails;
  githubIntegration: GitHubIntegration;
  onDataChange: (data: GitHubIntegration) => void;
}

/**
 * Step 3 props (Goals)
 */
export interface Step3Props extends StepComponentProps {
  userDetails: UserDetails;
  githubIntegration: GitHubIntegration;
}

/**
 * Step 4 props (final step - uses onComplete instead of onNext)
 */
export interface Step4Props {
  userDetails: UserDetails;
  githubIntegration: GitHubIntegration;
  onBack: () => void;
  onComplete: () => void;
}
