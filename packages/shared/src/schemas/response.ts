import { z } from "zod";
import { UUIDSchema, DateTimeSchema } from "./common";

export const ResponseActionTypeSchema = z.enum([
  "block_ip",
  "rate_limit",
  "add_header",
  "modify_header",
  "update_waf_rule",
  "revoke_session",
  "force_reauth",
  "disable_endpoint",
  "patch_vulnerability",
  "add_auth_check",
  "enable_csp",
  "enable_hsts",
  "custom"
]);
export type ResponseActionType = z.infer<typeof ResponseActionTypeSchema>;

export const ResponseSchema = z.object({
  id: UUIDSchema,
  episodeId: UUIDSchema,
  detectionId: UUIDSchema.optional(),
  actionType: ResponseActionTypeSchema,
  parameters: z.record(z.unknown()).default({}),
  target: z.string().optional(),
  success: z.boolean(),
  result: z.record(z.unknown()).default({}),
  error: z.string().optional(),
  appliedAt: DateTimeSchema.optional(),
  revertedAt: DateTimeSchema.optional(),
  timestamp: DateTimeSchema,
  createdAt: DateTimeSchema
});
export type Response = z.infer<typeof ResponseSchema>;

export const ResponseListParamsSchema = z.object({
  episodeId: UUIDSchema,
  detectionId: UUIDSchema.optional(),
  actionType: ResponseActionTypeSchema.optional(),
  success: z.boolean().optional(),
  dateFrom: DateTimeSchema.optional(),
  dateTo: DateTimeSchema.optional(),
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(50)
});
export type ResponseListParams = z.infer<typeof ResponseListParamsSchema>;

export const ResponseStatsSchema = z.object({
  totalResponses: z.number().int().nonnegative(),
  successfulResponses: z.number().int().nonnegative(),
  failedResponses: z.number().int().nonnegative(),
  byActionType: z.record(z.object({
    total: z.number().int().nonnegative(),
    successful: z.number().int().nonnegative()
  })),
  averageResponseTimeSeconds: z.number().nonnegative()
});
export type ResponseStats = z.infer<typeof ResponseStatsSchema>;