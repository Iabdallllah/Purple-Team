import { z } from "zod";

export function validateSchema<T>(schema: z.ZodSchema<T>, data: unknown): { success: true; data: T } | { success: false; errors: z.ZodError } {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { success: false, errors: result.error };
}

export function formatZodError(error: z.ZodError): string {
  return error.errors.map(e => `${e.path.join(".")}: ${e.message}`).join("; ");
}

export class ValidationError extends Error {
  constructor(public readonly errors: z.ZodError) {
    super(formatZodError(errors));
    this.name = "ValidationError";
  }
}

export function assertValid<T>(schema: z.ZodSchema<T>, data: unknown): T {
  const result = validateSchema(schema, data);
  if (!result.success) {
    throw new ValidationError(result.errors);
  }
  return result.data;
}