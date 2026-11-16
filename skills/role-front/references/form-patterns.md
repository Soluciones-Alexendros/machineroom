# Form Patterns

## Overview

Validation, submission, and UX patterns for forms. Validation messages match server errors; disable double-submit.

## Patterns

### Controlled Form with Validation

```tsx
function LoginForm() {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (values: FormValues) => {
    const newErrors: Record<string, string> = {};
    if (!values.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(values.email)) newErrors.email = 'Invalid email';
    if (!values.password) newErrors.password = 'Password is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const values = Object.fromEntries(formData);

    if (!validate(values)) return;
    setSubmitting(true);

    try {
      await api.login(values);
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.fieldErrors || { form: err.message });
      } else {
        setErrors({ form: 'Unexpected error' });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Field name="email" label="Email" error={errors.email} />
      <Field name="password" type="password" label="Password" error={errors.password} />
      {errors.form && <FormError>{errors.form}</FormError>}
      <Button type="submit" disabled={submitting}>
        {submitting ? 'Signing in…' : 'Sign in'}
      </Button>
    </form>
  );
}
```

### Server Error Mapping

```typescript
// Server returns: { fieldErrors: { email: 'Already registered' } }
// Client maps to form fields
const handleApiError = (error: ApiError) => {
  if (error.fieldErrors) {
    setErrors(error.fieldErrors);
  } else if (error.status === 401) {
    setErrors({ form: 'Invalid credentials' });
  } else {
    setErrors({ form: error.message });
  }
};
```

### Prevent Double Submit

```tsx
const handleSubmit = async () => {
  if (submittingRef.current) return; // Guard
  submittingRef.current = true;
  setSubmitting(true);

  try {
    await submit();
  } finally {
    submittingRef.current = false;
    setSubmitting(false);
  }
};

// Or use button disabled state
<Button type="submit" disabled={submitting}>Submit</Button>
```

### Accessible Form Fields

```tsx
function Field({ name, label, error, ...props }) {
  const id = useId();
  const errorId = error ? `${id}-error` : undefined;

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        name={name}
        aria-invalid={!!error}
        aria-describedby={errorId}
        aria-required={props.required}
        {...props}
      />
      {error && <span id={errorId} role="alert">{error}</span>}
    </div>
  );
}
```

### Multi-Step Forms

```tsx
function Wizard() {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<Partial<FormData>>({});

  const steps = [
    { title: 'Account', fields: ['email', 'password'] },
    { title: 'Profile', fields: ['name', 'avatar'] },
    { title: 'Confirm', fields: [] },
  ];

  const next = () => {
    if (validateStep(step)) setStep(s => s + 1);
  };

  const back = () => setStep(s => s - 1);

  return (
    <>
      <StepIndicator steps={steps} current={step} />
      <form onSubmit={handleSubmit}>
        <StepContent step={step} data={data} setData={setData} />
        <div className="actions">
          {step > 0 && <Button type="button" onClick={back}>Back</Button>}
          {step === steps.length - 1 ? (
            <Button type="submit">Complete</Button>
          ) : (
            <Button type="button" onClick={next}>Next</Button>
          )}
        </div>
      </form>
    </>
  );
}
```

## References

- [React Hook Form](https://react-hook-form.com/)
- [Zod Validation](https://zod.dev/)
- [WAI-ARIA Form Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)