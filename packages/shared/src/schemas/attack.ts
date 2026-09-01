import { z } from "zod";
import { UUIDSchema, DateTimeSchema } from "./common";

export const AttackSchema = z.object({
  id: UUIDSchema,
  episodeId: UUIDSchema,
  techniqueId: z.string(),
  owaspCategory: z.string(),
  attackType: z.string(),
  success: z.boolean(),
  evidence: z.record(z.unknown()).default({}),
  confidence: z.number().min(0).max(1),
  payload: z.string().optional(),
  targetEndpoint: z.string().optional(),
  httpMethod: z.string().optional(),
  requestHeaders: z.record(z.string()).optional(),
  requestBody: z.string().optional(),
  responseStatus: z.number().int().optional(),
  responseBody: z.string().optional(),
  timestamp: DateTimeSchema,
  createdAt: DateTimeSchema
});
export type Attack = z.infer<typeof AttackSchema>;

export const AttackListParamsSchema = z.object({
  episodeId: UUIDSchema,
  techniqueId: z.string().optional(),
  owaspCategory: z.string().optional(),
  success: z.boolean().optional(),
  dateFrom: DateTimeSchema.optional(),
  dateTo: DateTimeSchema.optional(),
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(50)
});
export type AttackListParams = z.infer<typeof AttackListParamsSchema>;

export const AttackStatsSchema = z.object({
  totalAttacks: z.number().int().nonnegative(),
  successfulAttacks: z.number().int().nonnegative(),
  failedAttacks: z.number().int().nonnegative(),
  byTechnique: z.record(z.object({
    total: z.number().int().nonnegative(),
    successful: z.number().int().nonnegative()
  })),
  byOwaspCategory: z.record(z.object({
    total: z.number().int().nonnegative(),
    successful: z.number().int().nonnegative()
  }))
});
export type AttackStats = z.infer<typeof AttackStatsSchema>;