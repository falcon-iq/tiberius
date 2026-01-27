/**
 * Step 1: User Details
 */

import { useForm } from 'react-hook-form';
import type { Step1Props, UserDetails } from './types';

export const StepUserDetails = ({ userDetails, onNext, onDataChange }: Step1Props) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<UserDetails>({
    defaultValues: userDetails,
    mode: 'onBlur',
  });

  const onSubmit = (data: UserDetails) => {
    onDataChange(data);
    onNext();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Step 1: Your Details</h2>

        {/* First Name */}
        <div className="mb-4">
          <label htmlFor="firstName" className="mb-2 block text-sm font-medium text-foreground">
            First Name
          </label>
          <input
            id="firstName"
            type="text"
            {...register('firstName', {
              required: 'First name is required',
              validate: (value) => value.trim().length > 0 || 'First name cannot be blank',
            })}
            placeholder="Enter your first name"
            className={`w-full rounded-lg border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
              errors.firstName
                ? 'border-destructive focus:ring-destructive'
                : 'border-border focus:ring-primary'
            }`}
          />
          {errors.firstName && (
            <p className="mt-2 text-xs text-destructive">{errors.firstName.message}</p>
          )}
        </div>

        {/* Last Name */}
        <div className="mb-4">
          <label htmlFor="lastName" className="mb-2 block text-sm font-medium text-foreground">
            Last Name
          </label>
          <input
            id="lastName"
            type="text"
            {...register('lastName', {
              required: 'Last name is required',
              validate: (value) => value.trim().length > 0 || 'Last name cannot be blank',
            })}
            placeholder="Enter your last name"
            className={`w-full rounded-lg border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
              errors.lastName
                ? 'border-destructive focus:ring-destructive'
                : 'border-border focus:ring-primary'
            }`}
          />
          {errors.lastName && (
            <p className="mt-2 text-xs text-destructive">{errors.lastName.message}</p>
          )}
        </div>

        {/* LDAP Username */}
        <div className="mb-4">
          <label
            htmlFor="ldapUsername"
            className="mb-2 block text-sm font-medium text-foreground"
          >
            LDAP Username
          </label>
          <input
            id="ldapUsername"
            type="text"
            {...register('ldapUsername', {
              required: 'LDAP username is required',
              validate: (value) => value.trim().length > 0 || 'LDAP username cannot be blank',
            })}
            placeholder="Enter your LDAP username"
            className={`w-full rounded-lg border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
              errors.ldapUsername
                ? 'border-destructive focus:ring-destructive'
                : 'border-border focus:ring-primary'
            }`}
          />
          {errors.ldapUsername && (
            <p className="mt-2 text-xs text-destructive">{errors.ldapUsername.message}</p>
          )}
          <p className="mt-2 text-xs text-muted-foreground">
            This is your GitHub username without the company suffix
          </p>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={!isValid}
          className="rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </form>
  );
};
