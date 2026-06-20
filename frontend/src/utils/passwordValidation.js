export function validatePassword(password) {
  const errors = [];
  if (password.length < 8) errors.push("at least 8 characters");
  if (!/[a-zA-Z]/.test(password)) errors.push("at least 1 letter");
  if (!/[0-9]/.test(password)) errors.push("at least 1 number");
  return { valid: errors.length === 0, errors };
}
