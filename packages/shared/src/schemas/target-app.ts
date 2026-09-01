import { z } from "zod";
import { UUIDSchema, DateTimeSchema, PaginationParamsSchema, PaginatedResponseSchema } from "./common";

export const TargetAppTypeSchema = z.enum(["juice_shop", "dvwa", "custom"]);
export type TargetAppType = z.infer<typeof TargetAppTypeSchema>;

export const TargetAppStatusSchema = z.enum(["pending", "ready", "error", "deprecated"]);
export type TargetAppStatus = z.infer<typeof TargetAppStatusSchema>;

export const TargetAppConfigSchema = z.object({
  baseUrl: z.string().url().optional(),
  dockerImage: z.string().optional(),
  dockerTag: z.string().default("latest"),
  environment: z.record(z.string()).default({}),
  healthCheckPath: z.string().default("/"),
  healthCheckInterval: z.number().int().positive().default(30),
  resetScript: z.string().optional(),
  exposedPorts: z.array(z.number().int().positive()).default([80, 443]),
  resources: z.object({
    cpuLimit: z.string().optional(),
    memoryLimit: z.string().optional()
  }).optional()
});
export type TargetAppConfig = z.infer<typeof TargetAppConfigSchema>;

export const TargetAppSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  name: z.string().min(1).max(255),
  type: TargetAppTypeSchema,
  config: TargetAppConfigSchema,
  status: TargetAppStatusSchema.default("pending"),
  lastValidatedAt: DateTimeSchema.optional(),
  validationError: z.string().optional(),
  createdAt: DateTimeSchema,
  updatedAt: DateTimeSchema
});
export type TargetApp = z.infer<typeof TargetAppSchema>;

export const CreateTargetAppRequestSchema = z.object({
  projectId: UUIDSchema,
  name: z.string().min(1).max(255),
  type: TargetAppTypeSchema,
  config: TargetAppConfigSchema
});
export type CreateTargetAppRequest = z.infer<typeof CreateTargetAppRequestSchema>;

export const UpdateTargetAppRequestSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  config: TargetAppConfigSchema.partial().optional(),
  status: TargetAppStatusSchema.optional()
}).refine(data => Object.keys(data).length > 0, {
  message: "At least one field must be provided"
});
export type UpdateTargetAppRequest = z.infer<typeof UpdateTargetAppRequestSchema>;

export const ValidateTargetAppRequestSchema = z.object({
  targetAppId: UUIDSchema
});
export type ValidateTargetAppRequest = z.infer<typeof ValidateTargetAppRequestSchema>;

export const ValidateTargetAppResponseSchema = z.object({
  success: z.boolean(),
  status: TargetAppStatusSchema,
  error: z.string().optional(),
  details: z.record(z.unknown()).optional()
});
export type ValidateTargetAppResponse = z.infer<typeof ValidateTargetAppResponseSchema>;

export const TargetAppListParamsSchema = PaginationParamsSchema.extend({
  projectId: UUIDSchema.optional(),
  type: TargetAppTypeSchema.optional(),
  status: TargetAppStatusSchema.optional()
});
export type TargetAppListParams = z.infer<typeof TargetAppListParamsSchema>;

export const TargetAppListResponseSchema = PaginatedResponseSchema(TargetAppSchema);
export type TargetAppListResponse = z.infer<typeof TargetAppListResponseSchema>;