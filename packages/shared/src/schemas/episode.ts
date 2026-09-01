import { z } from "zod";
import { UUIDSchema, DateTimeSchema, PaginationParamsSchema, PaginatedResponseSchema } from "./common";

export const EpisodeStatusSchema = z.enum([
  "pending",
  "initializing",
  "running",
  "completed",
  "failed",
  "cancelled"
]);
export type EpisodeStatus = z.infer<typeof EpisodeStatusSchema>;

export const SafetyLevelSchema = z.enum(["passive", "active", "aggressive"]);
export type SafetyLevel = z.infer<typeof SafetyLevelSchema>;

export const EpisodeConstraintsSchema = z.object({
  maxDurationMinutes: z.number().int().positive().max(120).default(30),
  allowedTechniques: z.array(z.string()).default([]),
  safetyLevel: SafetyLevelSchema.default("active"),
  maxConcurrentAttacks: z.number().int().positive().default(3),
  stopOnFirstDetection: z.boolean().default(false),
  stopOnSuccessfulAttack: z.boolean().default(false)
});
export type EpisodeConstraints = z.infer<typeof EpisodeConstraintsSchema>;

export const EpisodeSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  targetAppId: UUIDSchema,
  scenario: z.string(),
  status: EpisodeStatusSchema.default("pending"),
  constraints: EpisodeConstraintsSchema,
  startedAt: DateTimeSchema.optional(),
  completedAt: DateTimeSchema.optional(),
  error: z.string().optional(),
  createdAt: DateTimeSchema,
  updatedAt: DateTimeSchema
});
export type Episode = z.infer<typeof EpisodeSchema>;

export const CreateEpisodeRequestSchema = z.object({
  projectId: UUIDSchema,
  targetAppId: UUIDSchema,
  scenario: z.string(),
  constraints: EpisodeConstraintsSchema.partial().optional()
});
export type CreateEpisodeRequest = z.infer<typeof CreateEpisodeRequestSchema>;

export const EpisodeListParamsSchema = PaginationParamsSchema.extend({
  projectId: UUIDSchema.optional(),
  targetAppId: UUIDSchema.optional(),
  scenario: z.string().optional(),
  status: EpisodeStatusSchema.optional(),
  dateFrom: DateTimeSchema.optional(),
  dateTo: DateTimeSchema.optional()
});
export type EpisodeListParams = z.infer<typeof EpisodeListParamsSchema>;

export const EpisodeListResponseSchema = PaginatedResponseSchema(EpisodeSchema);
export type EpisodeListResponse = z.infer<typeof EpisodeListResponseSchema>;

export const EpisodeDetailSchema = EpisodeSchema.extend({
  targetApp: z.object({
    id: UUIDSchema,
    name: z.string(),
    type: z.string()
  }).optional(),
  attacks: z.array(z.object({
    id: UUIDSchema,
    techniqueId: z.string(),
    owaspCategory: z.string(),
    success: z.boolean(),
    confidence: z.number().min(0).max(1),
    timestamp: DateTimeSchema
  })).default([]),
  detections: z.array(z.object({
    id: UUIDSchema,
    attackId: UUIDSchema.optional(),
    detected: z.boolean(),
    detectionType: z.string(),
    confidence: z.number().min(0).max(1),
    timestamp: DateTimeSchema
  })).default([]),
  responses: z.array(z.object({
    id: UUIDSchema,
    detectionId: UUIDSchema.optional(),
    actionType: z.string(),
    success: z.boolean(),
    timestamp: DateTimeSchema
  })).default([]),
  score: z.object({
    detectionRate: z.number().min(0).max(1),
    mttrSeconds: z.number().nonnegative(),
    coverage: z.record(z.number().min(0).max(1)),
    overallScore: z.number().min(0).max(100)
  }).optional()
});
export type EpisodeDetail = z.infer<typeof EpisodeDetailSchema>;